/**
 * Tree View Module
 * 
 * Implements package-explorer-style tree visualization for graph data.
 * Supports expand/collapse functionality and cycle detection.
 */

class TreeView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.state = {
            expanded: new Set(),
        };
        this.graphSnapshot = null;
    }

    /**
     * Extract a display label from a node's attributes
     */
    nodeLabel(node) {
        if (!node) {
            return 'unknown';
        }
        const attrs = node.attributes || {};
        return attrs.name || attrs.Name || attrs.first || attrs.label || node.id;
    }

    /**
     * Determine root nodes for tree visualization
     * For directed graphs: nodes with zero in-degree
     * For undirected graphs: pick first node
     * Also includes disconnected components as separate roots
     */
    pickRoots(nodes, adjacency, directed) {
        if (!nodes.length) {
            return [];
        }

        if (!directed) {
            return [nodes[0].id];
        }

        const indegree = Object.create(null);
        for (const node of nodes) {
            indegree[node.id] = 0;
        }

        for (const nodeId of Object.keys(adjacency)) {
            for (const childId of adjacency[nodeId]) {
                if (indegree[childId] !== undefined) {
                    indegree[childId] += 1;
                }
            }
        }

        const roots = nodes
            .filter(node => indegree[node.id] === 0)
            .map(node => node.id);

        if (!roots.length) {
            roots.push(nodes[0].id);
        }

        // Ensure disconnected components are visible in the tree as extra roots
        const visited = new Set();
        const stack = [...roots];
        while (stack.length) {
            const current = stack.pop();
            if (visited.has(current)) {
                continue;
            }
            visited.add(current);
            for (const child of adjacency[current] || []) {
                if (!visited.has(child)) {
                    stack.push(child);
                }
            }
        }

        for (const node of nodes) {
            if (!visited.has(node.id)) {
                roots.push(node.id);
            }
        }

        return roots;
    }

    /**
     * Build tree data structure from raw graph
     */
    buildTreeData(rawGraph) {
        const nodes = rawGraph.nodes || [];
        const edges = rawGraph.edges || [];
        const directed = Boolean(rawGraph.directed);

        const nodesById = new Map(nodes.map(node => [node.id, node]));
        const adjacency = Object.create(null);
        for (const node of nodes) {
            adjacency[node.id] = [];
        }

        for (const edge of edges) {
            if (adjacency[edge.source]) {
                adjacency[edge.source].push(edge.target);
            }
            if (!directed && adjacency[edge.target]) {
                adjacency[edge.target].push(edge.source);
            }
        }

        const roots = this.pickRoots(nodes, adjacency, directed);
        return { nodesById, adjacency, roots, directed };
    }

    /**
     * Ensure at least one root is expanded on initial render
     */
    ensureRootExpanded(roots) {
        if (!roots.length) {
            return;
        }
        if (this.state.expanded.size === 0) {
            this.state.expanded.add(roots[0]);
        }
    }

    /**
     * Create DOM element for a single tree node with expand/collapse functionality
     */
    createTreeNodeElement(nodeId, treeData, ancestry) {
        const { nodesById, adjacency } = treeData;
        const node = nodesById.get(nodeId);
        const children = adjacency[nodeId] || [];

        const row = document.createElement('div');
        row.className = 'tree-row';
        row.dataset.nodeId = nodeId; // Store node ID for hover lookup

        const toggle = document.createElement('button');
        toggle.className = 'tree-toggle';
        toggle.type = 'button';

        const title = document.createElement('span');
        title.className = 'tree-label';
        title.textContent = node ? `${this.nodeLabel(node)} (${node.id})` : String(nodeId);
        title.dataset.nodeId = nodeId; // Store node ID for hover lookup

        // Add hover event listeners for cross-view highlighting
        title.addEventListener('mouseenter', () => {
            window.postMessage({
                type: 'node-hover',
                nodeId: nodeId
            }, '*');
        });

        title.addEventListener('mouseleave', () => {
            window.postMessage({
                type: 'node-hover-end',
                nodeId: nodeId
            }, '*');
        });

        row.appendChild(toggle);
        row.appendChild(title);

        const wrapper = document.createElement('div');
        wrapper.className = 'tree-node';
        wrapper.appendChild(row);

        if (!children.length) {
            toggle.textContent = '·';
            toggle.disabled = true;
            toggle.classList.add('is-leaf');
            return wrapper;
        }

        const childrenBox = document.createElement('div');
        childrenBox.className = 'tree-children';
        wrapper.appendChild(childrenBox);

        const isExpanded = this.state.expanded.has(nodeId);
        toggle.textContent = isExpanded ? '-' : '+';

        const renderChildren = () => {
            childrenBox.innerHTML = '';
            if (!this.state.expanded.has(nodeId)) {
                childrenBox.style.display = 'none';
                return;
            }

            childrenBox.style.display = 'block';
            const nextAncestry = new Set(ancestry);
            nextAncestry.add(nodeId);

            for (const childId of children) {
                if (nextAncestry.has(childId)) {
                    // Cycle detected
                    const cycle = document.createElement('div');
                    cycle.className = 'tree-cycle';
                    cycle.textContent = `↺ ${childId}`;
                    childrenBox.appendChild(cycle);
                    continue;
                }
                childrenBox.appendChild(this.createTreeNodeElement(childId, treeData, nextAncestry));
            }
        };

        toggle.addEventListener('click', () => {
            if (this.state.expanded.has(nodeId)) {
                this.state.expanded.delete(nodeId);
                toggle.textContent = '+';
            } else {
                this.state.expanded.add(nodeId);
                toggle.textContent = '-';
            }
            renderChildren();
        });

        renderChildren();
        return wrapper;
    }

    /**
     * Render tree view from current graph snapshot
     */
    renderFromSnapshot() {
        const canvas = document.getElementById(this.canvasId);
        if (!canvas) {
            return;
        }

        if (!this.graphSnapshot || !(this.graphSnapshot.nodes || []).length) {
            canvas.innerHTML = '<div class="tree-empty">Load a graph to see Tree View</div>';
            return;
        }

        const treeData = this.buildTreeData(this.graphSnapshot);
        this.ensureRootExpanded(treeData.roots);

        canvas.innerHTML = '';
        const rootList = document.createElement('div');
        rootList.className = 'tree-root-list';

        for (const rootId of treeData.roots) {
            rootList.appendChild(this.createTreeNodeElement(rootId, treeData, new Set()));
        }

        canvas.appendChild(rootList);
    }

    /**
     * Fetch graph data from server and refresh tree view
     */
    async refresh(graphLoaded) {
        if (!graphLoaded) {
            this.graphSnapshot = null;
            this.renderFromSnapshot();
            return;
        }

        try {
            const res = await fetch('/api/graph');
            const data = await res.json();
            if (!data.ok) {
                throw new Error(data.error || 'Graph snapshot not available');
            }
            this.graphSnapshot = data;
            this.renderFromSnapshot();
        } catch {
            const canvas = document.getElementById(this.canvasId);
            if (canvas) {
                canvas.innerHTML = '<div class="tree-empty">Tree View unavailable</div>';
            }
        }
    }

    /**
     * Clear tree state (e.g., expanded nodes)
     */
    clearState() {
        this.state.expanded.clear();
    }

    /**
     * Highlight a node in the tree view
     */
    highlightNode(nodeId) {
        const canvas = document.getElementById(this.canvasId);
        if (!canvas) return;

        const labels = canvas.querySelectorAll('.tree-label');
        labels.forEach(label => {
            if (label.dataset.nodeId === String(nodeId)) {
                label.classList.add('hovered');
            }
        });
    }

    /**
     * Remove highlight from a node in the tree view
     */
    unhighlightNode(nodeId) {
        const canvas = document.getElementById(this.canvasId);
        if (!canvas) return;

        const labels = canvas.querySelectorAll('.tree-label');
        labels.forEach(label => {
            if (label.dataset.nodeId === String(nodeId)) {
                label.classList.remove('hovered');
            }
        });
    }
}

// Export for use in templates
window.TreeView = TreeView;
