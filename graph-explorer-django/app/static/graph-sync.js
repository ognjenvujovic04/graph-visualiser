(() => {
    let currentVisualizer = "simple";
    let currentGraphData = null;

    async function postJson(url, body) {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body || {}),
        });
        return res.json();
    }

    function renderVisualizerOutput(markup) {
        const container = document.getElementById("main-canvas");
        if (!container) return;

        container.innerHTML = "";
        const frame = document.createElement("iframe");
        frame.setAttribute("sandbox", "allow-scripts allow-same-origin");
        frame.style.width = "100%";
        frame.style.height = "100%";
        frame.style.border = "0";
        frame.srcdoc = String(markup || "<html><body></body></html>");
        container.appendChild(frame);
    }

    async function applyVisualizerMode(visualizerId) {
        if (!API || !API.visualize) return;

        const data = await postJson(API.visualize, {
            visualizer: visualizerId,
            width: 1100,
            height: 700,
        });

        if (data.error) {
            alert(data.error);
            return;
        }

        renderVisualizerOutput(data.rendered);
    }

    function normalizeVisualizer(value) {
        const v = String(value || "").toLowerCase();
        return v === "block" ? "block" : "simple";
    }

    function resolveVisualizerFromUI() {
        const switchSelect = document.getElementById("visualizer-id-switch");
        const createSelect = document.getElementById("visualizer-id");
        if (switchSelect && switchSelect.value) return normalizeVisualizer(switchSelect.value);
        if (createSelect && createSelect.value) return normalizeVisualizer(createSelect.value);
        return currentVisualizer;
    }

    function wireVisualizerSelects() {
        const controls = [
            document.getElementById("visualizer-id"),
            document.getElementById("visualizer-id-switch"),
        ].filter(Boolean);

        currentVisualizer = resolveVisualizerFromUI();

        for (const ctrl of controls) {
            ctrl.addEventListener("change", async () => {
                currentVisualizer = normalizeVisualizer(ctrl.value);
                if (currentGraphData) {
                    drawTree(currentGraphData);
                }
                await applyVisualizerMode(currentVisualizer);
            });
        }
    }

    function wireModeButtons() {
        const buttons = Array.from(document.querySelectorAll(".mode-button[data-visualizer]"));
        if (!buttons.length) return;

        for (const btn of buttons) {
            btn.addEventListener("click", async () => {
                const visualizer = btn.getAttribute("data-visualizer") || "simple";
                currentVisualizer = visualizer;
                buttons.forEach(b => b.classList.toggle("is-active", b === btn));
                await applyVisualizerMode(visualizer);
                if (currentGraphData) {
                    drawTree(currentGraphData);
                }
            });
        }

        const active = buttons.find(b => b.classList.contains("is-active")) || buttons[0];
        if (active) {
            currentVisualizer = active.getAttribute("data-visualizer") || "simple";
            applyVisualizerMode(currentVisualizer);
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        wireModeButtons();
        wireVisualizerSelects();
        currentVisualizer = resolveVisualizerFromUI();

        if (typeof INITIAL_GRAPH !== "undefined" && INITIAL_GRAPH?.node_count > 0) {
            drawTree(INITIAL_GRAPH);
        }
    });

    function drawTree(data) {
        currentGraphData = data;
        const container = document.getElementById("tree-canvas");
        d3.select(container).selectAll("*").remove();
        const oldTip = document.getElementById("_tip");
        if (oldTip) oldTip.remove();

        if (!data.nodes || !data.nodes.length) {
            container.innerHTML = '<p style="padding:2rem;text-align:center;color:#5b655c;font-weight:700">Nema čvorova</p>';
            return;
        }

        const nodeMap  = new Map(data.nodes.map(n => [n.id, n]));
        const children = new Map(data.nodes.map(n => [n.id, []]));
        const inDeg    = new Map(data.nodes.map(n => [n.id, 0])); //broj dolaznih grana (za nalaženje rootova)

        const edges = data.edges || data.links || [];
        for (const e of edges) {
            const s = String(e.source), t = String(e.target);
            if (!nodeMap.has(s) || !nodeMap.has(t) || s === t) continue;
            children.get(s).push(t);
            inDeg.set(t, (inDeg.get(t) || 0) + 1);
        }

        const treeKids = new Map(data.nodes.map(n => [n.id, []]));
        const seen = new Set();

        function bfsFrom(startId) {
            if (seen.has(startId)) return;
            seen.add(startId);
            const q = [startId];
            while (q.length) {
                const pid = q.shift();
                for (const cid of children.get(pid) || []) {
                    if (seen.has(cid)) continue;
                    seen.add(cid);
                    treeKids.get(pid).push(cid);
                    q.push(cid);
                }
            }
        }
        const forestRootIds = [];
        const candidateRoots = data.nodes
            .filter(n => (inDeg.get(n.id) || 0) === 0)
            .map(n => n.id);

        for (const rid of candidateRoots) {
            if (!seen.has(rid)) {
                forestRootIds.push(rid);
                bfsFrom(rid);
            }
        }
        for (const n of data.nodes) {
            if (!seen.has(n.id)) {
                forestRootIds.push(n.id);
                bfsFrom(n.id);
            }
        }
        function nodeLabel(id) {
            const a = nodeMap.get(id)?.attributes || {};
            return a.name || a.label || a.title || id;
        }
        function buildH(id) {
            return { id, name: nodeLabel(id), children: treeKids.get(id).map(buildH) };
        }
        const W   = container.clientWidth || 400;
        const svg = d3.select(container).append("svg").style("display", "block");
        const zoomLayer = svg.append("g");
        const g   = zoomLayer.append("g");

        const zoom = d3.zoom()
            .scaleExtent([0.25, 4])
            .on("start", () => svg.style("cursor", "grabbing"))
            .on("zoom", (event) => {
                zoomLayer.attr("transform", event.transform);
            })
            .on("end", () => svg.style("cursor", "grab"));

        svg.call(zoom);
        svg.on("dblclick.zoom", null);
        svg.style("cursor", "grab");

        const isBlockMode = currentVisualizer === "block";
        const BLOCK_W = 220;
        const BLOCK_X = -(BLOCK_W / 2);
        const layout = d3.tree().nodeSize(isBlockMode ? [320, 200] : [140, 55]);
        const hasSuperRoot = forestRootIds.length > 1;
        const hierarchyInput = hasSuperRoot
            ? { id: "__forest__", name: "Forest", children: forestRootIds.map(buildH) }
            : buildH(forestRootIds[0]);
        const hier = d3.hierarchy(hierarchyInput);

        hier.descendants().forEach(d => {
            if (d.depth > 1 && d.children) {
                d._children = d.children;
                d.children  = null;
            }
        });

        const tip = document.createElement("div");
        tip.id = "_tip";
        Object.assign(tip.style, {
            position: "fixed", display: "none", background: "#1f2a1f",
            color: "#e8f4f1", fontSize: "12px", padding: "6px 10px",
            borderRadius: "8px", pointerEvents: "none", zIndex: "9999",
            maxWidth: "220px", lineHeight: "1.6",
            boxShadow: "0 4px 16px rgba(0,0,0,.35)"
        });
        document.body.appendChild(tip);
        document.addEventListener("mousemove", ev => {
            if (tip.style.display === "block") {
                tip.style.left = (ev.clientX + 14) + "px";
                tip.style.top  = (ev.clientY - 8) + "px";
            }
        });

        function render() {
            layout(hier);
            const allNodes = hier.descendants();
            const allLinks = hier.links();
            const nodes = hasSuperRoot ? allNodes.filter(d => d.depth > 0) : allNodes;
            const links = hasSuperRoot ? allLinks.filter(d => d.source.depth > 0) : allLinks;
            const yShift = hasSuperRoot && nodes.length ? Math.min(...nodes.map(d => d.y)) : 0;

            const leftXs  = nodes.map(d => isBlockMode ? d.x - (BLOCK_W / 2) : d.x - 12);
            const rightXs = nodes.map(d => isBlockMode ? d.x + (BLOCK_W / 2) : d.x + 12);
            const minX = Math.min(...leftXs), maxX = Math.max(...rightXs);
            const maxY = Math.max(...nodes.map(d => d.y));
            const PAD  = isBlockMode ? 90 : 50;
            const svgW = Math.max(W, maxX - minX + PAD * 2);
            const svgH = maxY + PAD * 2;
            svg.attr("width", svgW).attr("height", svgH);
            const shiftX = PAD - minX;
            g.attr("transform", `translate(${shiftX},${PAD})`);

            const link = g.selectAll(".lnk").data(links, d => d.target.data.id);
            link.enter().append("path").attr("class", "lnk")
                .attr("fill", "none").attr("stroke", "#9db39d").attr("stroke-width", 1.5)
                .merge(link)
                .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y - yShift));
            link.exit().remove();

            const node = g.selectAll(".nd").data(nodes, d => d.data.id);

            const enter = node.enter().append("g")
                .attr("class", "nd")
                .attr("transform", d => `translate(${d.x},${d.y - yShift})`)
                .style("cursor", "pointer")
                .on("click", (ev, d) => {
                    ev.stopPropagation();
                    if (d.children)       { d._children = d.children; d.children = null; }
                    else if (d._children) { d.children = d._children; d._children = null; }
                    render();
                })
                .on("mouseover", (ev, d) => {
                    const attrs = nodeMap.get(d.data.id)?.attributes || {};
                    const rows  = Object.entries(attrs)
                        .map(([k, v]) => `<span style="color:#9db39d">${k}:</span> ${v}`)
                        .join("<br>") || "<em>nema atributa</em>";
                    tip.innerHTML = `<strong style="color:#f4b942;display:block;margin-bottom:3px">${d.data.name}</strong>${rows}`;
                    tip.style.display = "block";
                })
                .on("mouseout", () => { tip.style.display = "none"; });

            if (isBlockMode) {
                enter.append("rect")
                    .attr("class", "blk-box")
                    .attr("x", BLOCK_X)
                    .attr("y", -40)
                    .attr("width", BLOCK_W)
                    .attr("rx", 8)
                    .attr("ry", 8)
                    .attr("fill", "#ffffff")
                    .attr("stroke", "#5b8fa8")
                    .attr("stroke-width", 1.5);

                enter.append("rect")
                    .attr("class", "blk-head")
                    .attr("x", BLOCK_X)
                    .attr("y", -40)
                    .attr("width", BLOCK_W)
                    .attr("height", 30)
                    .attr("rx", 8)
                    .attr("ry", 8)
                    .attr("fill", "#5b8fa8");

                enter.append("text")
                    .attr("class", "blk-title")
                    .attr("x", BLOCK_X + 8)
                    .attr("y", -21)
                    .style("font-size", "12px")
                    .style("font-family", "Manrope,sans-serif")
                    .style("font-weight", "700")
                    .style("fill", "#ffffff")
                    .style("pointer-events", "none");

                enter.append("text")
                    .attr("class", "blk-badge")
                    .attr("text-anchor", "end")
                    .attr("x", (BLOCK_W / 2) - 10)
                    .attr("y", -21)
                    .style("font-size", "14px")
                    .style("font-family", "monospace")
                    .style("font-weight", "800")
                    .style("fill", "#ffffff")
                    .style("pointer-events", "none");

                enter.append("text")
                    .attr("class", "blk-attrs")
                    .attr("x", BLOCK_X + 8)
                    .attr("y", -4)
                    .style("font-size", "11px")
                    .style("font-family", "monospace")
                    .style("fill", "#26322a")
                    .style("pointer-events", "none");
            } else {
                enter.append("circle").attr("r", 10);
                enter.append("text").attr("class", "badge")
                    .attr("text-anchor", "middle").attr("dy", "0.35em")
                    .style("font-size", "12px").style("font-weight", "800")
                    .style("fill", "#fff").style("pointer-events", "none");
                enter.append("text").attr("class", "lbl")
                    .attr("text-anchor", "middle").attr("dy", "1.9em")
                    .style("font-size", "11px").style("font-family", "Manrope,sans-serif")
                    .style("pointer-events", "none");
            }

            const merged = node.merge(enter).attr("transform", d => `translate(${d.x},${d.y - yShift})`);

            if (isBlockMode) {
                merged.select(".blk-title").text(d => {
                    const attrs = nodeMap.get(d.data.id)?.attributes || {};
                    const preferred = attrs.name || attrs.label || attrs.title || d.data.id;
                    return `${d.data.id} | ${preferred}`;
                });

                merged.select(".blk-badge").text(d => (d.children ? "-" : d._children ? "+" : ""));

                merged.select(".blk-attrs").each(function(d) {
                    const attrs = nodeMap.get(d.data.id)?.attributes || {};
                    const allLines = Object.entries(attrs).map(([k, v]) => `${k}: ${v}`);
                    const maxRows = 6;
                    const lines = allLines.slice(0, maxRows);
                    if (allLines.length > maxRows) {
                        lines.push(`... +${allLines.length - maxRows} more`);
                    }
                    const text = d3.select(this);
                    text.selectAll("tspan").remove();

                    if (!lines.length) {
                        text.append("tspan")
                            .attr("x", BLOCK_X + 8)
                            .attr("dy", "1.2em")
                            .text("(no attributes)");
                    } else {
                        lines.forEach((line, idx) => {
                            text.append("tspan")
                                .attr("x", BLOCK_X + 8)
                                .attr("dy", idx === 0 ? "1.2em" : "1.2em")
                                .text(line);
                        });
                    }

                    const rows = Math.max(lines.length, 1);
                    const bodyHeight = rows * 15 + 18;
                    d3.select(this.parentNode).select(".blk-box")
                        .attr("height", 30 + bodyHeight);
                });
            } else {
                merged.select("circle")
                    .attr("fill",         d => d._children ? "#157a6e" : "#e8f4f1")
                    .attr("stroke",       d => d._children ? "#0f5850" : "#157a6e")
                    .attr("stroke-width", 2);

                merged.select(".badge").text(d => d.children ? "-" : d._children ? "+" : "");
                merged.select(".lbl").text(d => d.data.name);
            }

            node.exit().remove();
        }

        render();
    }

})();