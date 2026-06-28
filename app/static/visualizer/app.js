const nodesEl = document.querySelector("#nodes");
const objectsEl = document.querySelector("#objects");
const uploadForm = document.querySelector("#upload-form");
const fileInput = document.querySelector("#file-input");
const resetNodesButton = document.querySelector("#reset-nodes");
const eventEl = document.querySelector("#event");
const uploadMsEl = document.querySelector("#upload-ms");
const downloadMsEl = document.querySelector("#download-ms");
const recoveryMsEl = document.querySelector("#recovery-ms");

let state = {
  nodes: [],
  objects: [],
  metrics: {},
};

function formatMs(value) {
  return value === null || value === undefined ? "-" : `${value} ms`;
}

function setBusy(isBusy) {
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = isBusy;
  });
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || response.statusText);
  }

  return response.json();
}

function shardsFor(nodeId, diskId) {
  return state.objects
    .flatMap((object) =>
      object.shards
        .filter((shard) => shard.node_id === nodeId && shard.disk_id === diskId)
        .map((shard) => ({ ...shard, objectName: object.name }))
    )
    .sort((a, b) => a.shard_index - b.shard_index);
}

function renderMetrics() {
  const metrics = state.metrics || {};
  uploadMsEl.textContent = formatMs(metrics.upload_ms);
  downloadMsEl.textContent = formatMs(metrics.download_ms);
  recoveryMsEl.textContent = formatMs(metrics.recovery_ms);
  eventEl.textContent = metrics.last_event || "ready";
}

function renderNodes() {
  nodesEl.innerHTML = "";

  state.nodes.forEach((node) => {
    const nodeEl = document.createElement("article");
    nodeEl.className = `node ${node.status}`;
    nodeEl.innerHTML = `
      <div class="node-head">
        <h2>${node.node_id}</h2>
        <span class="status">${node.status}</span>
      </div>
      <button class="danger delete-node" type="button" data-node="${node.node_id}">Delete Node</button>
    `;

    node.disks.forEach((disk) => {
      const diskEl = document.createElement("section");
      diskEl.className = "disk";
      diskEl.innerHTML = `<div class="disk-name">${disk.disk_id}</div><div class="shard-list"></div>`;
      const shardList = diskEl.querySelector(".shard-list");
      const shards = shardsFor(node.node_id, disk.disk_id);

      if (shards.length === 0) {
        shardList.innerHTML = `<div class="shard-meta">empty</div>`;
      }

      shards.forEach((shard) => {
        const shardEl = document.createElement("div");
        shardEl.className = `shard ${shard.type} ${shard.exists ? "" : "missing"}`;
        shardEl.innerHTML = `
          <div class="shard-index">S${shard.shard_index}</div>
          <div class="shard-meta">${shard.type} · ${shard.exists ? shard.objectName : "missing"}</div>
        `;
        shardList.appendChild(shardEl);
      });

      nodeEl.appendChild(diskEl);
    });

    nodesEl.appendChild(nodeEl);
  });
}

function renderObjects() {
  objectsEl.innerHTML = "";

  if (state.objects.length === 0) {
    objectsEl.innerHTML = `<p class="empty">No objects yet.</p>`;
    return;
  }

  state.objects.forEach((object) => {
    const objectEl = document.createElement("article");
    objectEl.className = "object";
    objectEl.innerHTML = `
      <div class="object-title">
        <span>${object.name}</span>
        <span>#${object.id}</span>
      </div>
      <div class="object-meta">
        ${object.size} bytes · ${object.missing_shards.length} missing · ${object.recoverable ? "recoverable" : "not recoverable"}
      </div>
      <div class="object-actions">
        <button class="primary recover-object" type="button" data-object="${object.id}">Recover</button>
        <button class="delete-object" type="button" data-object="${object.id}">Delete Object</button>
      </div>
    `;
    objectsEl.appendChild(objectEl);
  });
}

function render() {
  renderMetrics();
  renderNodes();
  renderObjects();
}

async function refresh() {
  state = await requestJson("/api/visualizer/state");
  render();
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  setBusy(true);

  try {
    await requestJson("/api/visualizer/upload", {
      method: "POST",
      body: formData,
    });
    fileInput.value = "";
    await refresh();
  } catch (error) {
    eventEl.textContent = error.message;
  } finally {
    setBusy(false);
  }
});

document.addEventListener("click", async (event) => {
  const deleteNode = event.target.closest(".delete-node");
  const recoverObject = event.target.closest(".recover-object");
  const deleteObject = event.target.closest(".delete-object");

  try {
    if (deleteNode) {
      setBusy(true);
      state = await requestJson(`/api/visualizer/nodes/${deleteNode.dataset.node}/delete`, {
        method: "POST",
      });
      render();
    }

    if (recoverObject) {
      setBusy(true);
      await requestJson(`/api/visualizer/recover/${recoverObject.dataset.object}`);
      await refresh();
    }

    if (deleteObject) {
      setBusy(true);
      await requestJson(`/api/visualizer/objects/${deleteObject.dataset.object}`, {
        method: "DELETE",
      });
      await refresh();
    }
  } catch (error) {
    eventEl.textContent = error.message;
  } finally {
    setBusy(false);
  }
});

resetNodesButton.addEventListener("click", async () => {
  setBusy(true);

  try {
    state = await requestJson("/api/visualizer/nodes/reset", {
      method: "POST",
    });
    render();
  } catch (error) {
    eventEl.textContent = error.message;
  } finally {
    setBusy(false);
  }
});

refresh();
setInterval(refresh, 5000);
