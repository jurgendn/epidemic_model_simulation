const container = document.getElementById("container");
container.style.width = window.innerWidth + "px";
container.style.height = window.innerHeight + "px";

let searchBox = document.getElementById("searchNode");

let dt;

let s = new sigma({
  renderer: {
    container: document.getElementById("container"),
    type: "canvas",
  },
  settings: {
    defaultEdgeType: "curvedArrow",
    autoRescale: true,
  },
});

fetch("data.json")
  .then((response) => response.json())
  .then((data) => {
    s.graph.read(data);
    s.graph.edges().forEach((edge) => {
      edge.color = edge._color;
    });
    
    s.graph.nodes().forEach((node) => {
      node.color = node._color;
    });
    s.refresh();
  });

// $.ajax({
//   async: false,
//   global: false,
//   url: "data.json",
//   dataType: "json",
//   success: function (dt) {
//     data = dt;
//   },
// });

// s.graph.read(dt);

// s.graph.edges().forEach((edge) => {
//   edge.color = edge._color;
// });

// s.graph.nodes().forEach((node) => {
//   node.color = node._color;
// });

// s.renderers[0].snapshot({ format: "jpg", background: "white", download: true });

// s.refresh();

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
  document.getElementById("p_quarantine").innerText =
    n.data.node.quarantine_date;
});
s.bind("outNode", function (n) {
  document.getElementById("p_name").innerText = "";
  document.getElementById("p_onset").innerText = "";
  document.getElementById("p_announce").innerText = "";
  document.getElementById("p_rank").innerText = "";
  document.getElementById("p_quarantine").innerText = "";
});

// console.log(data);
searchBox.addEventListener("keyup", function (evt) {
  if (evt.key === "Enter") {
    const nodeName = searchBox.value;
    s.graph.nodes().forEach((node) => {
      if (node.label === nodeName) {
        node.color = "#00ff80";
        node.size = 5;
      }
    });
  }
});
