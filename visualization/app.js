let width = window.innerWidth;
height = window.innerHeight - 20;

let stage = new PIXI.Container();

let app = new PIXI.Application({
  width,
  height,
  transparent: true,
});

document.body.appendChild(app.renderer.view);

let data;

$.ajax({
  async: false,
  global: false,
  url: "data.json",
  dataType: "json",
  success: function (dt) {
    data = dt;
    data.edges.forEach((edge) => {
      edge.gfx = new PIXI.Graphics();
    });
    data.nodes.forEach((node) => {
      node.gfx = new PIXI.Graphics();
      node.gfx.zIndex = 10;
      node.gfx.beginFill(0xff3200, 0.8);
      node.gfx.drawCircle(0, 0, 2);
      node.gfx.endFill();
      node.interactive = true;
      // node.on("pointerdown", onButtonDown);
      stage.addChild(node.gfx);
    });
  },
});

let edges = new PIXI.Graphics();

let simulation = d3
  .forceSimulation()
  .force(
    "edges",
    d3.forceLink().id((d) => d.id)
  )
  .force("charge", d3.forceManyBody().strength(-5))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .nodes(data.nodes)
  .on("tick", ticked);

simulation.force("edges").links(data.edges);

function ticked() {
  data.nodes.forEach((node) => {
    let { x, y, gfx } = node;
    gfx.position = new PIXI.Point(x, y);
  });
  edges.clear();
  edges.alpha = 0.6;
  data.edges.forEach((edge) => {
    let { source, target } = edge;
    edges.lineStyle(10, 0xc1eaea);
    edges.moveTo(source.x, source.y);
    edges.lineTo(target.x, target.y);
  });

  edges.endFill();

  app.renderer.render(stage);
}
