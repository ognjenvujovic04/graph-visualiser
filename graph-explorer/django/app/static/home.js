(function () {
    const config = window.GRAPH_EXPLORER_CONFIG || {};

    const pluginSelect = document.getElementById("plugin-id");
    const pathInput = document.getElementById("graph-path");
    const idKeyInput = document.getElementById("id-key");
    const refKeyInput = document.getElementById("ref-key");
    const stringRefsCheckbox = document.getElementById("treat-string-refs");
    const birdCanvas = document.getElementById("bird-view-canvas");

    const defaultPathsElement = document.getElementById("default-paths-data");
    const defaultPaths = defaultPathsElement
        ? JSON.parse(defaultPathsElement.textContent)
        : {};

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

    function renderBirdView(data) {
        if (!birdCanvas) return;

        clearContainer(birdCanvas);

        const width = birdCanvas.clientWidth || 220;
        const height = birdCanvas.clientHeight || 160;

        const svg = d3.select(birdCanvas)
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const nodes = data.nodes || [];
        const links = data.links || [];

        if (!nodes.length) {
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("fill", "#666")
                .text("No graph data");
            return;
        }

        const radius = Math.min(width, height) * 0.35;
        const centerX = width / 2;
        const centerY = height / 2;
        const nodePositions = new Map();

        nodes.forEach((node, index) => {
            const angle = (2 * Math.PI * index) / Math.max(nodes.length, 1);
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            nodePositions.set(node.id, { x, y });
        });

        svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("x1", d => nodePositions.get(d.source)?.x ?? centerX)
            .attr("y1", d => nodePositions.get(d.source)?.y ?? centerY)
            .attr("x2", d => nodePositions.get(d.target)?.x ?? centerX)
            .attr("y2", d => nodePositions.get(d.target)?.y ?? centerY)
            .attr("stroke", "#aeb8ae")
            .attr("stroke-width", 1);

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", d => {
                const p = nodePositions.get(d.id);
                return `translate(${p.x},${p.y})`;
            });

        node.append("circle")
            .attr("r", 6)
            .attr("fill", "#157a6e");

        node.append("title")
            .text(d => d.id);
    }

    async function renderBirdViewFromBackend() {
        try {
            const data = await loadGraphData();
            renderBirdView(data);
        } catch (err) {
            if (birdCanvas) {
                birdCanvas.innerHTML = `<div style="color:#a33;font-weight:700;">${err.message}</div>`;
            }
        }
    }

    if (pluginSelect) {
        pluginSelect.addEventListener("change", (event) => {
            applyDefaultsForPlugin(event.target.value);
        });
    }

    renderBirdViewFromBackend();
})();