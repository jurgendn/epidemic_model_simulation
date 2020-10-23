let width = window.innerWidth;
height = window.innerHeight - 20;

let stage = new PIXI.Container();
let renderer = new PIXI.Renderer({
  width,
  height,
  transparent: true,
});

// let viewport = new Viewport();
// stage.addChild(viewport);

// viewport.plugins.add();
document.body.appendChild(renderer.view);

let data;

$.ajax({
  async: false,
  global: false,
  url: "data.json",
  dataType: "json",
  success: function (dt) {
    data = dt;
    drawEdges(data);
    drawNodes(data);
  },
});

function drawNodes(data) {
  data.nodes.forEach((node) => {
    node.gfx = new PIXI.Graphics();
    node.gfx.zIndex = 10;
    node.gfx.beginFill(0x412369, node.size);
    node.gfx.drawCircle(0, 0, node.size);
    node.gfx.endFill();
    stage.addChild(node.gfx);
  });
}

function drawEdges(data) {
  data.edges.forEach((edge) => {
    edge.gfx = new PIXI.Graphics();
  });
}

// d3.select(renderer.view).call(
//   d3
//     .drag()
//     .container(renderer.view)
//     .subject(() => simulation.find(d3.event.x, d3.event.y))
//     .on("start", dragstarted)
//     .on("drag", dragged)
//     .on("end", dragended)
// );

let simulation = d3
  .forceSimulation()
  .force(
    "edges",
    d3.forceLink().id((d) => d.id)
  )
  .force("charge", d3.forceManyBody().strength(2))
  .force("center", d3.forceCenter(width / 2, height / 2));

simulation.nodes(data.nodes).on("tick", ticked);

simulation.force("edges").links(data.edges);

let edges = new PIXI.Graphics();
stage.addChild(edges);

function ticked() {
  data.nodes.forEach((node) => {
    let { x, y, gfx } = node;
    gfx.position = new PIXI.Point(x, y);
  });

  edges.clear();
  edges.alpha = 0.6;

  data.edges.forEach((edge) => {
    let { source, target } = edge;
    edges.lineStyle(edge.size/20, 0xc1eaea);
    edges.moveTo(source.x, source.y);
    edges.lineTo(target.x, target.y);
  });

  edges.endFill();
  renderer.render(stage);
}

function dragstarted() {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d3.event.subject.fx = d3.event.subject.x;
  d3.event.subject.fy = d3.event.subject.y;
}

function dragged() {
  d3.event.subject.fx = d3.event.x;
  d3.event.subject.fy = d3.event.y;
}

function dragended() {
  if (!d3.event.active) simulation.alphaTarget(0);
  d3.event.subject.fx = null;
  d3.event.subject.fy = null;
}
