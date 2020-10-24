const container = document.getElementById("container");
container.style.width = window.innerWidth * 0.8 + "px";
container.style.height = window.innerHeight * 0.8 + "px";

let data;

let s = new sigma({
  renderer: {
    container: document.getElementById("container"),
    type: "canvas",
  },
  settings: {
    defaultEdgeType: "curve",
    labelThreshold: 11,
  },
});

$.ajax({
  async: false,
  global: false,
  url: "data.json",
  dataType: "json",
  success: function (dt) {
    data = dt;
  },
});

s.graph.read(data);

s.graph.edges().forEach((edge) => {
  edge.color = edge._color;
});

s.graph.nodes().forEach((node) => {
  node.color = node._color;
});

s.refresh();

let dragListener = sigma.plugins.dragNodes(s, s.renderers[0]);

dragListener.bind("startdrag", function (event) {
  console.log(event);
});
dragListener.bind("drag", function (event) {
  console.log(event);
});
dragListener.bind("drop", function (event) {
  console.log(event);
});
dragListener.bind("dragend", function (event) {
  console.log(event);
});

s.bind("overNode", function (n) {
  document.getElementById("p_name").innerText = n.data.node.full_name;
  document.getElementById("p_onset").innerText = n.data.node.onset_date;
  document.getElementById("p_announce").innerText = n.data.node.announce_date;
  document.getElementById("p_rank").innerText = n.data.node.pagerank;
});
s.bind("outNode", function (n) {
  document.getElementById("p_name").innerText = "";
  document.getElementById("p_onset").innerText = "";
  document.getElementById("p_announce").innerText = "";
  document.getElementById("p_rank").innerText = "";
});
