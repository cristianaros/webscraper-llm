import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { SourcesPanel } from "./SourcesPanel";
import { RunsPanel } from "./RunsPanel";
import { ReviewPanel } from "./ReviewPanel";
export function CollectionAdmin({token}:{token:string}){const[tab,setTab]=useState("sources");return <Tabs value={tab} onValueChange={setTab} className="mx-auto mt-10 max-w-screen-xl px-6"><TabsList><TabsTrigger value="sources">Fuentes</TabsTrigger><TabsTrigger value="runs">Ejecuciones</TabsTrigger><TabsTrigger value="review">Revisión</TabsTrigger></TabsList><TabsContent value="sources"><SourcesPanel token={token}/></TabsContent><TabsContent value="runs"><RunsPanel token={token} active={tab==="runs"}/></TabsContent><TabsContent value="review"><ReviewPanel token={token}/></TabsContent></Tabs>}
