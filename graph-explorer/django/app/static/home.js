(function () {
    const config = window.GRAPH_EXPLORER_CONFIG || {};

    const pluginSelect = document.getElementById("plugin-id");
    const pathInput = document.getElementById("graph-path");
    const idKeyInput = document.getElementById("id-key");
    const refKeyInput = document.getElementById("ref-key");
    const stringRefsCheckbox = document.getElementById("treat-string-refs");
    const birdCanvas = document.getElementById("bird-canvas");

    const defaultPathsElement = document.getElementById("default-paths-data");
    const defaultPaths = defaultPathsElement
        ? JSON.parse(defaultPathsElement.textContent)
        : {};

    let currentGraphData = null;
    let currentSelectedNodeId = null;
    let currentViewport = null;
    let currentLayoutPositions = null;
    let currentLinks = null;
    let currentMainSize = { width: 760, height: 520 };
    let currentContentBounds = null;

    function applyDefaultsForPlugin(pluginId) {
        const normalized = (pluginId || "").toLowerCase();

        if (defaultPaths[normalized] && pathInput) {
            pathInput.value = defaultPaths[normalized];
        }

        if (normalized === "json" || normalized === "xml") {
            if (idKeyInput) idKeyInput.value = "@id";
            if (refKeyInput) refKeyInput.value = "@ref";
            if (stringRefsCheckbox) stringRefsCheckbox.checked = true;
        } else if (normalized === "csv") {
            if (idKeyInput) idKeyInput.value = "id";
            if (refKeyInput) refKeyInput.value = "ref";
            if (stringRefsCheckbox) stringRefsCheckbox.checked = true;
        }
    }

    async function loadGraphData() {
        const response = await fetch(config.graphDataUrl);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to load graph data");
        }

        return data;
    }

    function clearContainer(container) {
        if (container) {
            container.innerHTML = "";
        }
    }

    function computeCircularPositions(nodes, width, height) {
        const nodePositions = new Map();

        if (nodes.length === 1) {
            nodePositions.set(nodes[0].id, { x: width / 2, y: height / 2 });
            return nodePositions;
        }

        const radius = Math.min(width, height) * 0.34;
        const centerX = width / 2;
        const centerY = height / 2;

        nodes.forEach((node, index) => {
            const angle = (2 * Math.PI * index) / nodes.length;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            nodePositions.set(node.id, { x, y });
        });

        return nodePositions;
    }

    function computeBoundsFromPositions(positions) {
        const values = Array.from(positions.values());
        if (!values.length) return null;

        const minX = Math.min(...values.map(p => p.x));
        const maxX = Math.max(...values.map(p => p.x));
        const minY = Math.min(...values.map(p => p.y));
        const maxY = Math.max(...values.map(p => p.y));

        const pad = 30;

        return {
            minX: minX - pad,
            maxX: maxX + pad,
            minY: minY - pad,
            maxY: maxY + pad
        };
    }

    function buildScaledLayoutPositions(width, height) {
        if (!currentLayoutPositions || !currentLayoutPositions.size) {
            return null;
        }

        const bounds = computeBoundsFromPositions(currentLayoutPositions);
        currentContentBounds = bounds;

        if (!bounds) return null;

        const contentWidth = Math.max(bounds.maxX - bounds.minX, 1);
        const contentHeight = Math.max(bounds.maxY - bounds.minY, 1);

        const scale = Math.min(width / contentWidth, height / contentHeight);
        const scaledWidth = contentWidth * scale;
        const scaledHeight = contentHeight * scale;

        const offsetX = (width - scaledWidth) / 2;
        const offsetY = (height - scaledHeight) / 2;

        const result = new Map();

        currentLayoutPositions.forEach((pos, id) => {
            result.set(id, {
                x: offsetX + (pos.x - bounds.minX) * scale,
                y: offsetY + (pos.y - bounds.minY) * scale
            });
        });

        return {
            positions: result,
            bounds,
            scale,
            offsetX,
            offsetY
        };
    }

    function renderBirdView(data) {
        if (!birdCanvas) return;

        currentGraphData = data;
        clearContainer(birdCanvas);

        const width = birdCanvas.clientWidth || 220;
        const height = birdCanvas.clientHeight || 160;

        const svg = d3.select(birdCanvas)
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const root = svg.append("g").attr("class", "bird-root");
        const linksLayer = root.append("g").attr("class", "bird-links");
        const nodesLayer = root.append("g").attr("class", "bird-nodes");
        const overlayLayer = svg.append("g").attr("class", "bird-overlay");

        const nodes = data.nodes || [];
        const links = currentLinks || data.links || data.edges || [];

        if (!nodes.length) {
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#666")
                .text("No graph data");
            return;
        }

        let nodePositions;
        const scaledLayout = buildScaledLayoutPositions(width, height);

        if (scaledLayout && scaledLayout.positions.size) {
            nodePositions = scaledLayout.positions;
        } else {
            nodePositions = computeCircularPositions(nodes, width, height);
        }

        linksLayer
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("x1", d => {
                const sourceId = typeof d.source === "object" ? d.source.id : d.source;
                return nodePositions.get(sourceId)?.x ?? width / 2;
            })
            .attr("y1", d => {
                const sourceId = typeof d.source === "object" ? d.source.id : d.source;
                return nodePositions.get(sourceId)?.y ?? height / 2;
            })
            .attr("x2", d => {
                const targetId = typeof d.target === "object" ? d.target.id : d.target;
                return nodePositions.get(targetId)?.x ?? width / 2;
            })
            .attr("y2", d => {
                const targetId = typeof d.target === "object" ? d.target.id : d.target;
                return nodePositions.get(targetId)?.y ?? height / 2;
            })
            .attr("stroke", "#aeb8ae")
            .attr("stroke-width", 1);

        const nodeGroups = nodesLayer
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", d => {
                const p = nodePositions.get(d.id);
                return `translate(${p.x},${p.y})`;
            });

        nodeGroups.append("circle")
            .attr("r", d => d.id === currentSelectedNodeId ? 8 : 6)
            .attr("fill", d => d.id === currentSelectedNodeId ? "#f4b942" : "#157a6e")
            .attr("stroke", d => d.id === currentSelectedNodeId ? "#8a5a00" : "none")
            .attr("stroke-width", d => d.id === currentSelectedNodeId ? 2 : 0);

        nodeGroups.append("title")
            .text(d => d.id);

        if (currentViewport) {
            overlayLayer.append("rect")
                .attr("x", currentViewport.x)
                .attr("y", currentViewport.y)
                .attr("width", currentViewport.width)
                .attr("height", currentViewport.height)
                .attr("fill", "rgba(244,185,66,0.10)")
                .attr("stroke", "#f4b942")
                .attr("stroke-width", 2)
                .attr("rx", 4)
                .attr("ry", 4);
        }
    }

    function updateBirdSelection(nodeId) {
        currentSelectedNodeId = nodeId || null;
        if (currentGraphData) {
            renderBirdView(currentGraphData);
        }
    }

    function updateBirdLayout(messageData) {
        const positions = messageData?.positions || [];
        currentLinks = messageData?.links || currentLinks;

        if (!positions.length) return;

        const map = new Map();
        positions.forEach(pos => {
            if (pos && pos.id != null && pos.x != null && pos.y != null) {
                map.set(pos.id, { x: Number(pos.x), y: Number(pos.y) });
            }
        });

        currentLayoutPositions = map;

        if (currentGraphData) {
            renderBirdView(currentGraphData);
        }
    }

    function updateBirdViewport(messageData) {
        if (!messageData || !messageData.transform) {
            currentViewport = null;
        } else {
            const transform = messageData.transform;
            const mainWidth = messageData.width || currentMainSize.width || 760;
            const mainHeight = messageData.height || currentMainSize.height || 520;

            currentMainSize = {
                width: mainWidth,
                height: mainHeight
            };

            const birdWidth = birdCanvas?.clientWidth || 220;
            const birdHeight = birdCanvas?.clientHeight || 160;

            const visibleLeft = -transform.x / transform.k;
            const visibleTop = -transform.y / transform.k;
            const visibleWidth = mainWidth / transform.k;
            const visibleHeight = mainHeight / transform.k;

            if (currentLayoutPositions && currentLayoutPositions.size && currentContentBounds) {
                const scaledLayout = buildScaledLayoutPositions(birdWidth, birdHeight);

                if (scaledLayout) {
                    const bounds = scaledLayout.bounds;
                    const scale = scaledLayout.scale;
                    const offsetX = scaledLayout.offsetX;
                    const offsetY = scaledLayout.offsetY;

                    currentViewport = {
                        x: offsetX + (visibleLeft - bounds.minX) * scale,
                        y: offsetY + (visibleTop - bounds.minY) * scale,
                        width: visibleWidth * scale,
                        height: visibleHeight * scale
                    };
                } else {
                    currentViewport = null;
                }
            } else {
                currentViewport = {
                    x: visibleLeft * (birdWidth / mainWidth),
                    y: visibleTop * (birdHeight / mainHeight),
                    width: visibleWidth * (birdWidth / mainWidth),
                    height: visibleHeight * (birdHeight / mainHeight)
                };
            }
        }

        if (currentGraphData) {
            renderBirdView(currentGraphData);
        }
    }

    async function renderBirdViewFromBackend() {
        try {
            const data = await loadGraphData();
            currentLinks = data.links || data.edges || [];
            renderBirdView(data);
        } catch (err) {
            if (birdCanvas) {
                birdCanvas.innerHTML = `<div style="color:#a33;font-weight:700;">${err.message}</div>`;
            }
        }
    }

    function handleVisualizerPayload(payload) {
        if (!payload || typeof payload !== "object") return;
        if (!payload.type) return;

        if (payload.type === "node-select") {
            updateBirdSelection(payload.data?.nodeId);
        }

        if (payload.type === "viewport-change") {
            updateBirdViewport(payload.data);
        }

        if (payload.type === "visualizer-positions" || payload.type === "layout-complete") {
            updateBirdLayout(payload.data);
        }

        if (payload.type === "graph-ready") {
            if (payload.data?.width && payload.data?.height) {
                currentMainSize = {
                    width: payload.data.width,
                    height: payload.data.height
                };
            }
            renderBirdViewFromBackend();
        }
    }

    function handleVisualizerMessage(event) {
        handleVisualizerPayload(event.data);
    }

    function handleInlineVisualizerEvent(event) {
        handleVisualizerPayload(event.detail);
    }

    if (pluginSelect) {
        pluginSelect.addEventListener("change", (event) => {
            applyDefaultsForPlugin(event.target.value);
        });
    }

    window.addEventListener("message", handleVisualizerMessage);
    window.addEventListener("visualizer-event", handleInlineVisualizerEvent);
    window.addEventListener("resize", () => {
        if (currentGraphData) {
            renderBirdView(currentGraphData);
        }
    });

    renderBirdViewFromBackend();
})();