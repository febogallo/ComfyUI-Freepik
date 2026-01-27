/**
 * Freepik Status Display Extension
 * Shows real-time status, elapsed time, and cost on Freepik nodes
 */

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// Track active node states
const nodeStates = new Map();

// Status display configuration
const STATUS_CONFIG = {
    height: 50,
    fontSize: 12,
    padding: 10,
    colors: {
        idle: "#2a2a2a",
        waiting: "#3d3d1a",
        processing: "#1a3d2a",
        completed: "#1a4a1a",
        error: "#4a1a1a",
        cached: "#1a2a4a"
    },
    textColors: {
        idle: "#999999",
        waiting: "#ffff66",
        processing: "#66ffaa",
        completed: "#66ff66",
        error: "#ff6666",
        cached: "#6699ff"
    }
};

// Freepik node types that should have status display
const FREEPIK_NODES = [
    "FreepikUpscalerCreative",
    "FreepikUpscalerPrecision",
    "FreepikMystic",
    "FreepikRemoveBackground"
];

/**
 * Initialize status state for a node
 */
function initNodeState(nodeId) {
    if (!nodeStates.has(nodeId)) {
        nodeStates.set(nodeId, {
            status: "idle",
            statusText: "Ready",
            elapsed: 0,
            cost: 0,
            estimatedCost: 0,
            startTime: null,
            timerInterval: null
        });
    }
    return nodeStates.get(nodeId);
}

/**
 * Update node state and trigger redraw
 */
function updateNodeState(nodeId, updates) {
    const state = initNodeState(nodeId);
    Object.assign(state, updates);

    // Find and redraw the node
    if (app.graph) {
        const node = app.graph._nodes.find(n => n.id === nodeId);
        if (node) {
            node.setDirtyCanvas(true, true);
        }
    }
}

/**
 * Start elapsed time timer for a node
 */
function startTimer(nodeId) {
    const state = initNodeState(nodeId);

    if (state.timerInterval) {
        clearInterval(state.timerInterval);
    }

    state.startTime = Date.now();
    state.elapsed = 0;

    state.timerInterval = setInterval(() => {
        if (state.startTime) {
            state.elapsed = Math.floor((Date.now() - state.startTime) / 1000);
            if (app.graph) {
                const node = app.graph._nodes.find(n => n.id === nodeId);
                if (node) {
                    node.setDirtyCanvas(true, true);
                }
            }
        }
    }, 1000);
}

/**
 * Stop elapsed time timer for a node
 */
function stopTimer(nodeId) {
    const state = nodeStates.get(nodeId);
    if (state && state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
        state.startTime = null;
    }
}

/**
 * Format elapsed time as mm:ss
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Draw status bar at the bottom of the node
 */
function drawStatusBar(node, ctx) {
    // Initialize state if needed (handles case where ID changed after creation)
    const state = initNodeState(node.id);

    const { height, fontSize, padding, colors, textColors } = STATUS_CONFIG;
    const y = node.size[1] - height;
    const width = node.size[0];

    // Save context state
    ctx.save();

    // Background
    ctx.fillStyle = colors[state.status] || colors.idle;
    ctx.beginPath();
    ctx.roundRect(0, y, width, height, [0, 0, 8, 8]);
    ctx.fill();

    // Border
    ctx.strokeStyle = "#444444";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();

    // Status dot
    const dotRadius = 5;
    const dotX = padding + dotRadius;
    const dotY = y + height / 2;

    ctx.beginPath();
    ctx.arc(dotX, dotY, dotRadius, 0, Math.PI * 2);
    ctx.fillStyle = textColors[state.status] || textColors.idle;
    ctx.fill();

    // Status text
    ctx.fillStyle = textColors[state.status] || textColors.idle;
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";

    const textX = dotX + dotRadius + 8;
    ctx.fillText(`${state.statusText}`, textX, y + height / 2 - 8);

    // Info line
    ctx.font = `${fontSize - 1}px Arial, sans-serif`;
    let infoText = "";

    if (state.status === "processing" || state.status === "waiting") {
        infoText = `Time: ${formatTime(state.elapsed)}`;
        if (state.estimatedCost > 0) {
            infoText += ` | Est: EUR ${state.estimatedCost.toFixed(2)}`;
        }
    } else if (state.status === "completed") {
        infoText = `Time: ${formatTime(state.elapsed)} | Cost: EUR ${state.cost.toFixed(2)}`;
    } else if (state.status === "cached") {
        infoText = "No API call - using cache";
    } else if (state.status === "error") {
        infoText = "See console for details";
    }

    if (infoText) {
        ctx.fillStyle = "#aaaaaa";
        ctx.fillText(infoText, textX, y + height / 2 + 10);
    }

    // Restore context state
    ctx.restore();
}

/**
 * Register the extension
 */
app.registerExtension({
    name: "Freepik.StatusDisplay",

    async setup() {
        console.log("[Freepik] Setting up status display extension...");

        // Listen for status events
        api.addEventListener("freepik-status", (event) => {
            const detail = event.detail;
            // Convert node_id to number to match node.id type
            const nodeId = typeof detail.node_id === 'string' ? parseInt(detail.node_id, 10) : detail.node_id;

            console.log("[Freepik] Status event:", detail, "-> nodeId:", nodeId);

            switch (detail.event) {
                case "start":
                    startTimer(nodeId);
                    updateNodeState(nodeId, {
                        status: "waiting",
                        statusText: "Starting...",
                        estimatedCost: detail.estimated_cost || 0,
                        cost: 0
                    });
                    break;

                case "processing":
                    updateNodeState(nodeId, {
                        status: "processing",
                        statusText: detail.message || "Processing...",
                        estimatedCost: detail.estimated_cost || 0
                    });
                    break;

                case "polling":
                    updateNodeState(nodeId, {
                        status: "processing",
                        statusText: `${detail.api_status || "Processing"}...`,
                    });
                    break;

                case "completed":
                    stopTimer(nodeId);
                    updateNodeState(nodeId, {
                        status: "completed",
                        statusText: "Completed!",
                        cost: detail.cost || 0
                    });
                    setTimeout(() => {
                        updateNodeState(nodeId, {
                            status: "idle",
                            statusText: "Ready",
                            elapsed: 0
                        });
                    }, 8000);
                    break;

                case "cached":
                    updateNodeState(nodeId, {
                        status: "cached",
                        statusText: "Using Cache",
                        cost: 0,
                        elapsed: 0
                    });
                    setTimeout(() => {
                        updateNodeState(nodeId, {
                            status: "idle",
                            statusText: "Ready"
                        });
                    }, 5000);
                    break;

                case "error":
                    stopTimer(nodeId);
                    updateNodeState(nodeId, {
                        status: "error",
                        statusText: detail.message || "Error",
                        cost: 0
                    });
                    break;

                case "estimate":
                    updateNodeState(nodeId, {
                        estimatedCost: detail.estimated_cost || 0
                    });
                    break;
            }
        });

        // Listen for confirmation requests
        api.addEventListener("freepik-confirm", async (event) => {
            const detail = event.detail;
            // Convert node_id to number to match node.id type
            const nodeId = typeof detail.node_id === 'string' ? parseInt(detail.node_id, 10) : detail.node_id;

            const message = `Freepik API Request\n\n` +
                `Operation: ${detail.operation}\n` +
                `Estimated Cost: EUR ${detail.estimated_cost.toFixed(2)}\n` +
                `Output Size: ${detail.output_size}\n\n` +
                `Do you want to proceed?`;

            const confirmed = confirm(message);

            try {
                await api.fetchApi("/freepik/confirm_response", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        node_id: nodeId,
                        request_id: detail.request_id,
                        confirmed: confirmed
                    })
                });
            } catch (err) {
                console.error("[Freepik] Failed to send confirmation:", err);
            }

            if (!confirmed) {
                updateNodeState(nodeId, {
                    status: "idle",
                    statusText: "Cancelled",
                    elapsed: 0
                });
            }
        });

        console.log("[Freepik] Status display extension ready");
    },

    // Hook into node type registration - this is called BEFORE any node instances are created
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Check if this is a Freepik node by checking the node type name
        if (!FREEPIK_NODES.includes(nodeData.name)) {
            return;
        }

        console.log(`[Freepik] Registering status bar for node type: ${nodeData.name}`);

        // Store original onNodeCreated if it exists
        const origOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function() {
            // Call original if exists
            if (origOnNodeCreated) {
                origOnNodeCreated.apply(this, arguments);
            }

            // Node created - state will be initialized lazily when drawing

            // Store original onDrawBackground
            const origOnDrawBackground = this.onDrawBackground;

            // Override onDrawBackground to add status bar (has larger clipping area than foreground)
            this.onDrawBackground = function(ctx) {
                if (origOnDrawBackground) {
                    origOnDrawBackground.call(this, ctx);
                }
                drawStatusBar(this, ctx);
            };

            // Override computeSize to always include status bar height
            const origComputeSize = this.computeSize;
            this.computeSize = function() {
                const size = origComputeSize ? origComputeSize.apply(this, arguments) : [this.size[0], this.size[1]];
                // Ensure minimum height includes status bar
                size[1] = Math.max(size[1], 200) + STATUS_CONFIG.height;
                return size;
            };

            // Set initial size with status bar
            const currentSize = this.computeSize();
            this.size[0] = Math.max(this.size[0], currentSize[0]);
            this.size[1] = Math.max(this.size[1], currentSize[1]);

            // Mark as setup
            this._freepikSetup = true;
        };

        // Store original onRemoved
        const origOnRemoved = nodeType.prototype.onRemoved;

        nodeType.prototype.onRemoved = function() {
            if (origOnRemoved) {
                origOnRemoved.apply(this, arguments);
            }
            stopTimer(this.id);
            nodeStates.delete(this.id);
        };
    }
});

console.log("[Freepik] Status display extension loaded");
