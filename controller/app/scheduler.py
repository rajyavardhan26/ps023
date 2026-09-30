import logging
from typing import List, Optional
from controller.app.models import Node, NodeStatus
from controller.app.schemas import VMCreateRequest

logger = logging.getLogger("controller.scheduler")

class SchedulingError(Exception):
    pass

class ResourceAwareScheduler:
    """
    Weighted Resource-Aware Placement Scheduler for PS-023.
    Evaluates online nodes based on CPU headroom, RAM headroom, and active VM distribution.
    """

    @staticmethod
    def calculate_node_score(node: Node, vm_req: VMCreateRequest) -> float:
        # Memory headroom calculation (MB)
        free_memory_mb = node.memory_total - node.memory_used_mb
        if free_memory_mb < vm_req.memory_mb:
            return -1.0  # Ineligible: Not enough RAM

        # Normalized available memory (0.0 to 1.0)
        norm_free_mem = max(0.0, min(1.0, free_memory_mb / max(node.memory_total, 1)))

        # Normalized available CPU (0.0 to 1.0)
        norm_free_cpu = max(0.0, min(1.0, (100.0 - node.cpu_used_percent) / 100.0))

        # VM balance factor (nodes with fewer VMs get a slight balancing bonus)
        current_vms = len(node.vms) if node.vms else 0
        vm_balance = 1.0 / (1.0 + current_vms)

        # Weighted composite score (45% RAM headroom, 35% CPU headroom, 20% Balance)
        score = (norm_free_mem * 0.45) + (norm_free_cpu * 0.35) + (vm_balance * 0.20)
        return score

    @classmethod
    def select_node(cls, vm_req: VMCreateRequest, nodes: List[Node]) -> Node:
        """
        Selects the optimal node for VM placement.
        """
        if not nodes:
            raise SchedulingError("No compute nodes are registered in the cluster.")

        online_nodes = [n for n in nodes if n.status == NodeStatus.ONLINE]
        if not online_nodes:
            raise SchedulingError("All cluster nodes are currently OFFLINE or DEGRADED.")

        # If user explicitly preferred a specific node, validate capacity first
        if vm_req.preferred_node:
            for n in online_nodes:
                if n.node_id == vm_req.preferred_node:
                    if (n.memory_total - n.memory_used_mb) >= vm_req.memory_mb:
                        logger.info(f"Preferred node {n.node_id} accepted for VM '{vm_req.name}'")
                        return n
                    else:
                        raise SchedulingError(
                            f"Preferred node '{vm_req.preferred_node}' lacks sufficient RAM "
                            f"(Requested: {vm_req.memory_mb}MB, Free: {n.memory_total - n.memory_used_mb}MB)"
                        )
            raise SchedulingError(f"Preferred node '{vm_req.preferred_node}' is not online or does not exist.")

        # Score all candidate nodes
        best_node = None
        highest_score = -1.0

        for node in online_nodes:
            score = cls.calculate_node_score(node, vm_req)
            logger.info(f"Node '{node.node_id}' scored: {score:.3f}")
            if score > highest_score:
                highest_score = score
                best_node = node

        if not best_node or highest_score < 0:
            raise SchedulingError(
                f"Insufficient cluster resources to provision VM '{vm_req.name}' "
                f"(Requested: {vm_req.cpu} vCPUs, {vm_req.memory_mb}MB RAM)."
            )

        logger.info(f"Scheduler selected node '{best_node.node_id}' (score: {highest_score:.3f}) for VM '{vm_req.name}'")
        return best_node
