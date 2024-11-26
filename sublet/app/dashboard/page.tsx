"use client";

import { useState, useEffect } from "react";

import { fetchProperties } from "../../services/propertyService";
import { PropertyInterface } from "@/interfaces/Property";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { Button } from "@/components/ui/button";

import { PlusIcon } from "lucide-react";

import PropertyList from "@/components/custom/PropertyList";

import PropertyForm from "@/components/custom/PropertyForm";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import Image from "next/image";

const Dashboard = () => {
  const [properties, setProperties] = useState<PropertyInterface[]>([]);

  useEffect(() => {
    fetchProperties()
      .then((data) => {
        setProperties(data);
      })
      .catch((error) => {
        console.error("Error fetching properties:", error);
      });
  }, []);

  return (
    <div className="">

      <Tabs defaultValue="posted" className="">

        <div className="w-screen flex justify-end p-6 gap-4">
          <TabsList>
            <TabsTrigger value="posted">Posted</TabsTrigger>
            <TabsTrigger value="drafts">Drafts</TabsTrigger>
          </TabsList>
          <PropertyForm onNewProperty={setProperties}>
            <Button className="p-2 rounded-full">
              <PlusIcon className="w-5" />
            </Button>
          </PropertyForm>
        </div>


        <TabsContent value="posted" className="p-5">
          <div className="px-10 max-md:px-0">
            <div className="space-y-12">
              <h1 className="text-4xl tracking-tight font-bold">
                My Listings
              </h1>
              <PropertyList properties={properties} />
            </div>
          </div>
        </TabsContent>


        <TabsContent value="drafts" className="p-5">
          <div className="items-center flex flex-col justify-center px-10 max-md:px-0">
            <div className="space-y-12">
              <h1 className="text-4xl tracking-tight font-bold">
                My Drafts
              </h1>
              <PropertyList properties={properties} />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
