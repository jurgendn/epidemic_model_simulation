const container = document.getElementById("container");
container.style.width = window.outerWidth + "px";
container.style.height = window.outerHeight + "px";

let dt;

let s = new sigma({
  renderer: {
    container: document.getElementById("container"),
    type: "canvas",
  },
  settings: {
    // defaultEdgeType: "curvedArrow",
    autoRescale: true,
    drawLabel: true,
    labelThreshold: 1000,
    minNodeSize: 1,
    zoomMin: 0.00001,
    defaultLabelSize: 9,
  },
});

$("#fileName").on("keydown", function (e) {
  if (e.keyCode === 13 || e.which === 13) {
    let path = "data/" + this.value + ".json" || "data/hanoi_map.json";
    console.log(path);
    fetch(path)
      .then((response) => response.json())
      .then((data) => {
        s.graph.read(data);
        console.log(data);
        s.refresh();
      });
  }
});

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
