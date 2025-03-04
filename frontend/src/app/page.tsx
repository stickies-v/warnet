"use client";

import React, { useState } from "react";

import ForceGraph from "@/components/force-graph";
import Sidebar from "@/components/sidebar";
import { CANVAS_HEIGHT, CANVAS_WIDTH } from "@/config";
import { GraphNode } from "@/types";
import DialogBox from "@/components/dialog";
import { NodeGraphProvider } from "@/contexts/node-graph-context";

export default function Home() {
  // const [nodes, setNodes] = useState<GraphNode[]>([]);
  // const [links, setLinks] = useState([]);
  // const [isDialogOpen, setIsDialogOpen] = useState(false);

  // React.useEffect(() => {
  //   console.log("links", links);
  // }, [links]);

  // const addNode = () => {
  //   const newNode = {
  //     id: nodes.length,
  //     size: 10,
  //     x: CANVAS_WIDTH / 2,
  //     y: CANVAS_HEIGHT / 2,
  //   };
  //   setNodes([...nodes, newNode]);
  // };

  // const handleNodeDrag = (node: GraphNode) => {
  //   setNodes((prevNodes) =>
  //     prevNodes.map((n) => (n.id === node.id ? node : n))
  //   );
  // };
  return (
    <NodeGraphProvider>
      <main className="bg-black flex min-h-screen items-center justify-center">
        <DialogBox />
        <ForceGraph />
      </main>
    </NodeGraphProvider>
  );
}
