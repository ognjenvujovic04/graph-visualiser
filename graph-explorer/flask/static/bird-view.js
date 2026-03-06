/**
 * Bird View Module
 * 
 * Renders a zoomed-out view of the entire graph with a viewport rectangle
 * showing the current pan/zoom state of the main view.
 * Implements synchronization with the main visualizer's zoom and pan operations.
 */

class BirdView {
    constructor(canvasId) {
        this.canvasId = canvasId;
        this.container = document.getElementById(canvasId);
        this.svg = null;
        this.graphData = null;
        this.mainViewState = {
            transform: { x: 0, y: 0, k: 1 },
            width: 900,
            height: 600
        };
        this.birdViewScale = 1;
        this.renderPending = false;
        this.lastRenderTime = 0;
        this.minRenderInterval = 50; // Minimum 50ms between renders
        this.init();
    }

    /**
     * Initialize the bird view container with SVG
     */
    init() {
        if (!this.container) {
            console.warn('Bird view container not found');
            return;
        }

        // Get the actual container dimensions
        const width = this.container.clientWidth || 240;
        const height = this.container.clientHeight || 200;

        // Create SVG
        this.svg = d3.select(`#${this.canvasId}`)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .style('width', '100%')
            .style('height', '100%')
            .style('border', '1px solid #3c3c3c')
            .style('background', '#1a1a1a');

        // Add group for graph content
        this.graphGroup = this.svg.append('g');

        // Add viewport rectangle (shows current main view area)
        this.viewportRect = this.svg.append('rect')
            .attr('class', 'viewport-rect')
            .attr('fill', 'none')
            .attr('stroke', '#f4b942')
            .attr('stroke-width', 2)
            .attr('opacity', 0.8)
            .style('pointer-events', 'none');

        // Add click handler to center main view on clicked point
        this.svg.on('click', (event) => this.handleBirdViewClick(event));
    }

    /**
     * Update node positions from the main visualizer
     * Called when visualizer sends position data via postMessage
     */
    updateNodePositions(positions, links) {
        if (!this.graphData) {
            this.graphData = { nodes: [], edges: links || [] };
        }

        // Update nodes with positions
        const nodesById = new Map(this.graphData.nodes.map(n => [n.id, n]));
        positions.forEach(pos => {
            if (nodesById.has(pos.id)) {
                const node = nodesById.get(pos.id);
                node.x = pos.x;
                node.y = pos.y;
            }
        });

        if (links) {
            this.graphData.edges = links;
        }

        // Throttle rendering to avoid excessive updates
        const now = Date.now();
        if (now - this.lastRenderTime > this.minRenderInterval && !this.renderPending) {
            this.lastRenderTime = now;
            this.render();
            this.updateViewport();
        } else if (!this.renderPending) {
            // Schedule a render for later
            this.renderPending = true;
            setTimeout(() => {
                this.renderPending = false;
                this.lastRenderTime = Date.now();
                this.render();
                this.updateViewport();
            }, this.minRenderInterval);
        }
    }

    /**
     * Set graph data and render bird view
     */
    setGraphData(nodes, edges) {
        this.graphData = { nodes, edges };
        this.render();
    }

    /**
     * Calculate bounds of the graph nodes
     */
    calculateBounds(nodes) {
        if (!nodes || nodes.length === 0) {
            return { minX: 0, maxX: 100, minY: 0, maxY: 100 };
        }

        // Filter nodes that have valid positions
        const validNodes = nodes.filter(n => n.x !== undefined && n.y !== undefined && !isNaN(n.x) && !isNaN(n.y));
        
        if (validNodes.length === 0) {
            return { minX: 0, maxX: 100, minY: 0, maxY: 100 };
        }

        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;

        validNodes.forEach(node => {
            minX = Math.min(minX, node.x);
            maxX = Math.max(maxX, node.x);
            minY = Math.min(minY, node.y);
            maxY = Math.max(maxY, node.y);
        });

        // Add padding
        const padX = (maxX - minX) * 0.1 || 50;
        const padY = (maxY - minY) * 0.1 || 50;

        return {
            minX: minX - padX,
            maxX: maxX + padX,
            minY: minY - padY,
            maxY: maxY + padY
        };
    }

    /**
     * Render the bird view
     */
    render() {
        if (!this.graphData || !this.svg) {
            return;
        }

        let { nodes, edges } = this.graphData;
        const svgWidth = this.svg.node().clientWidth;
        const svgHeight = this.svg.node().clientHeight;

        if (!nodes || nodes.length === 0) {
            return;
        }

        // Create a map of nodes by ID for edge lookup
        const nodesById = new Map(nodes.map(n => [n.id, n]));

        // Convert edge references to use source/target objects if needed
        const processedEdges = edges.map(e => {
            const edge = { ...e };
            // If source/target are strings, convert to node references
            if (typeof edge.source === 'string') {
                edge.source = nodesById.get(edge.source) || { id: edge.source, x: 0, y: 0 };
            }
            if (typeof edge.target === 'string') {
                edge.target = nodesById.get(edge.target) || { id: edge.target, x: 0, y: 0 };
            }
            return edge;
        });

        // Calculate bounds
        const bounds = this.calculateBounds(nodes);
        const graphWidth = bounds.maxX - bounds.minX;
        const graphHeight = bounds.maxY - bounds.minY;
        const graphAspectRatio = graphWidth / graphHeight;

        // Calculate scale to fit graph in bird view while preserving aspect ratio
        const containerAspectRatio = svgWidth / svgHeight;
        let scale, offsetX, offsetY;

        if (graphAspectRatio > containerAspectRatio) {
            // Graph is wider than container
            scale = (svgWidth - 20) / graphWidth;
            offsetX = 10;
            offsetY = (svgHeight - graphHeight * scale) / 2;
        } else {
            // Graph is taller than container
            scale = (svgHeight - 20) / graphHeight;
            offsetX = (svgWidth - graphWidth * scale) / 2;
            offsetY = 10;
        }

        this.birdViewScale = scale;

        // Create scale functions that preserve aspect ratio
        const xScale = d3.scaleLinear()
            .domain([bounds.minX, bounds.maxX])
            .range([offsetX, offsetX + graphWidth * scale]);

        const yScale = d3.scaleLinear()
            .domain([bounds.minY, bounds.maxY])
            .range([offsetY, offsetY + graphHeight * scale]);

        // Store scales for viewport calculation
        this.xScale = xScale;
        this.yScale = yScale;

        // Update edges using enter/update/exit pattern for better performance
        const edgeSelection = this.graphGroup.selectAll('.bird-edge')
            .data(processedEdges, d => d.id || `${d.source.id}-${d.target.id}`);

        // Remove old edges
        edgeSelection.exit().remove();

        // Update existing edges
        edgeSelection
            .attr('x1', d => {
                const source = typeof d.source === 'object' ? d.source : nodesById.get(d.source);
                return xScale(source?.x || 0);
            })
            .attr('y1', d => {
                const source = typeof d.source === 'object' ? d.source : nodesById.get(d.source);
                return yScale(source?.y || 0);
            })
            .attr('x2', d => {
                const target = typeof d.target === 'object' ? d.target : nodesById.get(d.target);
                return xScale(target?.x || 0);
            })
            .attr('y2', d => {
                const target = typeof d.target === 'object' ? d.target : nodesById.get(d.target);
                return yScale(target?.y || 0);
            });

        // Add new edges
        edgeSelection.enter()
            .append('line')
            .attr('class', 'bird-edge')
            .attr('x1', d => {
                const source = typeof d.source === 'object' ? d.source : nodesById.get(d.source);
                return xScale(source?.x || 0);
            })
            .attr('y1', d => {
                const source = typeof d.source === 'object' ? d.source : nodesById.get(d.source);
                return yScale(source?.y || 0);
            })
            .attr('x2', d => {
                const target = typeof d.target === 'object' ? d.target : nodesById.get(d.target);
                return xScale(target?.x || 0);
            })
            .attr('y2', d => {
                const target = typeof d.target === 'object' ? d.target : nodesById.get(d.target);
                return yScale(target?.y || 0);
            })
            .attr('stroke', '#5b8fa8')
            .attr('stroke-width', 0.5)
            .attr('opacity', 0.5);

        // Update nodes using enter/update/exit pattern
        const validNodes = nodes.filter(n => n.x !== undefined && n.y !== undefined && !isNaN(n.x) && !isNaN(n.y));
        
        const nodeSelection = this.graphGroup.selectAll('.bird-node')
            .data(validNodes, d => d.id);

        // Remove old nodes
        nodeSelection.exit().remove();

        // Update existing nodes
        nodeSelection
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y));

        // Add new nodes
        nodeSelection.enter()
            .append('circle')
            .attr('class', 'bird-node')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', 2)
            .attr('fill', '#5b8fa8')
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.5)
            .attr('opacity', 0.8);

        // Update viewport rectangle
        this.updateViewport();
    }

    /**
     * Update viewport rectangle based on main view's transform
     */
    updateViewport() {
        if (!this.svg || !this.graphData) {
            return;
        }

        const { nodes } = this.graphData;
        if (!nodes || nodes.length === 0) {
            return;
        }

        // Use cached scales if available, otherwise recalculate
        let xScale = this.xScale;
        let yScale = this.yScale;

        if (!xScale || !yScale) {
            const bounds = this.calculateBounds(nodes);
            const svgWidth = this.svg.node().clientWidth;
            const svgHeight = this.svg.node().clientHeight;
            const graphWidth = bounds.maxX - bounds.minX;
            const graphHeight = bounds.maxY - bounds.minY;
            const graphAspectRatio = graphWidth / graphHeight;
            const containerAspectRatio = svgWidth / svgHeight;
            
            let scale, offsetX, offsetY;
            if (graphAspectRatio > containerAspectRatio) {
                scale = (svgWidth - 20) / graphWidth;
                offsetX = 10;
                offsetY = (svgHeight - graphHeight * scale) / 2;
            } else {
                scale = (svgHeight - 20) / graphHeight;
                offsetX = (svgWidth - graphWidth * scale) / 2;
                offsetY = 10;
            }

            xScale = d3.scaleLinear()
                .domain([bounds.minX, bounds.maxX])
                .range([offsetX, offsetX + graphWidth * scale]);

            yScale = d3.scaleLinear()
                .domain([bounds.minY, bounds.maxY])
                .range([offsetY, offsetY + graphHeight * scale]);
        }

        // Get main view state
        const mainViewWidth = this.mainViewState.width;
        const mainViewHeight = this.mainViewState.height;
        const transform = this.mainViewState.transform;

        // Calculate the visible region in graph coordinates
        // The visible width/height in graph space depends on zoom level
        const visibleGraphWidth = mainViewWidth / transform.k;
        const visibleGraphHeight = mainViewHeight / transform.k;

        // Calculate center of visible region in graph coordinates
        const mainViewCenterX = mainViewWidth / 2;
        const mainViewCenterY = mainViewHeight / 2;
        const graphCenterX = (mainViewCenterX - transform.x) / transform.k;
        const graphCenterY = (mainViewCenterY - transform.y) / transform.k;

        // Calculate the four corners of the visible region in graph coordinates
        const graphLeft = graphCenterX - visibleGraphWidth / 2;
        const graphRight = graphCenterX + visibleGraphWidth / 2;
        const graphTop = graphCenterY - visibleGraphHeight / 2;
        const graphBottom = graphCenterY + visibleGraphHeight / 2;

        // Convert to bird view pixel coordinates
        const birdLeft = xScale(graphLeft);
        const birdRight = xScale(graphRight);
        const birdTop = yScale(graphTop);
        const birdBottom = yScale(graphBottom);

        const birdWidth = Math.abs(birdRight - birdLeft);
        const birdHeight = Math.abs(birdBottom - birdTop);

        // Update viewport rectangle
        this.viewportRect
            .attr('x', Math.min(birdLeft, birdRight))
            .attr('y', Math.min(birdTop, birdBottom))
            .attr('width', Math.max(birdWidth, 5))
            .attr('height', Math.max(birdHeight, 5));
    }

    /**
     * Handle clicks on bird view to center main view
     */
    handleBirdViewClick(event) {
        if (!this.graphData) {
            return;
        }

        const { nodes } = this.graphData;
        if (!nodes || nodes.length === 0) {
            return;
        }

        const bounds = this.calculateBounds(nodes);
        const svgWidth = this.svg.node().clientWidth;
        const svgHeight = this.svg.node().clientHeight;

        // Get click coordinates relative to SVG
        const [mouseX, mouseY] = d3.pointer(event, this.svg.node());

        // Create inverse scale functions
        const xScale = d3.scaleLinear()
            .domain([bounds.minX, bounds.maxX])
            .range([10, svgWidth - 10]);

        const yScale = d3.scaleLinear()
            .domain([bounds.minY, bounds.maxY])
            .range([10, svgHeight - 10]);

        // Convert bird view coordinates back to graph coordinates
        const graphX = xScale.invert(mouseX);
        const graphY = yScale.invert(mouseY);

        // Dispatch event for main view to handle
        const event2 = new CustomEvent('bird-view-click', {
            detail: { x: graphX, y: graphY }
        });
        document.dispatchEvent(event2);
    }

    /**
     * Update main view transform state
     * Called from main visualizer when zoom/pan changes
     */
    updateMainViewState(transform, width, height) {
        this.mainViewState = { transform, width, height };
        
        // Throttle viewport updates for zoom/pan
        const now = Date.now();
        if (now - this.lastRenderTime > this.minRenderInterval && !this.renderPending) {
            this.lastRenderTime = now;
            this.updateViewport();
        } else if (!this.renderPending) {
            this.renderPending = true;
            setTimeout(() => {
                this.renderPending = false;
                this.lastRenderTime = Date.now();
                this.updateViewport();
            }, this.minRenderInterval);
        }
    }

    /**
     * Refresh the bird view (called after graph updates)
     */
    refresh(graphLoaded) {
        if (!graphLoaded) {
            // Clear bird view if no graph is loaded
            if (this.graphGroup) {
                this.graphGroup.selectAll('*').remove();
            }
            if (this.viewportRect) {
                this.viewportRect.attr('width', 0).attr('height', 0);
            }
            return;
        }
        // Re-render with current data
        if (this.graphData) {
            this.render();
        }
    }
}
