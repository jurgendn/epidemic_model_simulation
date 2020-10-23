const container = document.getElementById("container");
container.style.width = window.innerWidth + "px";
container.style.height = window.innerHeight + "px";

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

var dragListener = sigma.plugins.dragNodes(s, s.renderers[0]);

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
