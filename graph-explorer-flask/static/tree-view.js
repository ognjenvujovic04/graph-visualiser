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
     * Build tree data structure from raw graph
     */
    buildTreeData(rawGraph) {
        const nodes = rawGraph.nodes || [];
        const edges = rawGraph.edges || [];
        const directed = Boolean(rawGraph.directed);

        const nodeMap = new Map(nodes.map(node => [node.id, node]));
        const children = new Map(nodes.map(n => [n.id, []]));
        const inDeg = new Map(nodes.map(n => [n.id, 0]));

        // Build adjacency and calculate in-degree
        for (const e of edges) {
            const s = String(e.source);
            const t = String(e.target);
            if (!nodeMap.has(s) || !nodeMap.has(t) || s === t) {
                continue;
            }
            children.get(s).push(t);
            inDeg.set(t, (inDeg.get(t) || 0) + 1);
        }

        // BFS to build tree structure from a starting node
        const seen = new Set();
        const treeChildren = new Map(nodes.map(n => [n.id, []]));

        const bfsFrom = (startId) => {
            if (seen.has(startId)) {
                return;
            }
            seen.add(startId);
            const queue = [startId];
            while (queue.length) {
                const parentId = queue.shift();
                for (const childId of children.get(parentId) || []) {
                    if (seen.has(childId)) {
                        continue;
                    }
                    seen.add(childId);
                    treeChildren.get(parentId).push(childId);
                    queue.push(childId);
                }
            }
        };

        // Find roots: nodes with in-degree 0
        const forestRoots = [];
        const candidateRoots = nodes
            .filter(n => (inDeg.get(n.id) || 0) === 0)
            .map(n => n.id);

        for (const rootId of candidateRoots) {
            if (!seen.has(rootId)) {
                forestRoots.push(rootId);
                bfsFrom(rootId);
            }
        }

        // Add disconnected components as additional roots
        for (const n of nodes) {
            if (!seen.has(n.id)) {
                forestRoots.push(n.id);
                bfsFrom(n.id);
            }
        }

        return {
            nodeMap,
            children: treeChildren,
            roots: forestRoots,
            directed
        };
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
        const { nodeMap, children } = treeData;
        const node = nodeMap.get(nodeId);
        const childIds = children.get(nodeId) || [];

        const row = document.createElement('div');
        row.className = 'tree-row';
        row.dataset.nodeId = nodeId;

        const toggle = document.createElement('button');
        toggle.className = 'tree-toggle';
        toggle.type = 'button';

        const title = document.createElement('span');
        title.className = 'tree-label';
        title.textContent = node ? `${this.nodeLabel(node)} (${node.id})` : String(nodeId);
        title.dataset.nodeId = nodeId;

        // Add hover event listeners for cross-view highlighting
        title.addEventListener('mouseenter', () => {
            window.postMessage({
                type: 'node-hover',
                data: { nodeId: nodeId }
            }, '*');
        });

        title.addEventListener('mouseleave', () => {
            window.postMessage({
                type: 'node-hover-end',
                data: { nodeId: nodeId }
            }, '*');
        });

        row.appendChild(toggle);
        row.appendChild(title);

        const wrapper = document.createElement('div');
        wrapper.className = 'tree-node';
        wrapper.appendChild(row);

        if (!childIds.length) {
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

            for (const childId of childIds) {
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
