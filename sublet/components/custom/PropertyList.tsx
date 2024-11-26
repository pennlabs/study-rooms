import { AspectRatio } from "@radix-ui/react-aspect-ratio";
import Property from "./Property";
import { PropertyInterface } from "@/interfaces/Property";
import Image from "next/image";

interface PropertyListProps {
  properties: PropertyInterface[];
}

const PropertyList: React.FC<PropertyListProps> = ({ properties }) => {
  return (
    <>
      <ul className="grid xl:grid-cols-4 max-xl:grid-cols-3 max-lg:grid-cols-2 max-sm:grid-cols-1 gap-8 max-md:gap-5 list-none">
        {properties.map((property) => (
          <li key={property.id}>
            <Property property={property} />
          </li>
        ))}
      </ul>
    </>
  );
};

export default PropertyList;
