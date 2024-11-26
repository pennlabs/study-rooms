{/*
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { CheckIcon, DotsHorizontalIcon as Dots } from "@radix-ui/react-icons";
*/}

import { CalendarIcon, ImageIcon } from "@radix-ui/react-icons";
import { MapPinIcon, DollarSignIcon } from 'lucide-react';

import { Card, CardContent } from "@/components/ui/card"
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";

import Image from "next/image";

import { PropertyInterface, ImageInterface } from "@/interfaces/Property";
import { AspectRatio } from "../ui/aspect-ratio";
import { Skeleton } from "../ui/skeleton";

function formatDate(dateString: string): string {
  // Convert the input string to a Date object
  const date = new Date(dateString);

  // Format the date to the desired format
  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short', // Abbreviated month name
    day: 'numeric'  // Numeric day of the month
  });

  return formattedDate;
}

interface PropertyProps {
  property: PropertyInterface;
}

const Property: React.FC<PropertyProps> = ({ property }) => {
  return (
    <div className="relative space-y-1">

      <div className="absolute z-30 -top-2 -right-2">
        <span className="flex h-4 w-4 rounded-full bg-green-500" />
        <span className="flex h-4 w-4 rounded-full bg-green-500 animate-ping absolute top-0" />
      </div>

      {property.images.length > 0 ?
        <Carousel className="w-full rounded-xl overflow-hidden group">
          <CarouselContent>
            {property.images.map((_, index) => (
              <CarouselItem key={index}>
                <AspectRatio ratio={16 / 9}>
                  <Image
                    className="rounded-xl"
                    draggable="false"
                    src={property.images[index].image_url}
                    alt="Property image"
                    objectFit="cover"
                    fill
                  />
                </AspectRatio>
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselPrevious />
          <CarouselNext />
        </Carousel>
        :
        <AspectRatio ratio={16 / 9}>
          <Skeleton className="h-full flex items-center justify-center rounded-xl">
            <ImageIcon className="w-6 h-6" />
          </Skeleton>
        </AspectRatio>
      }

      <div className="flex justify-between pt-3 max-sm:flex-col max-sm:gap-3 max-sm:pb-3 pb-1">
        <div className="font-bold text-xl">{property.title}</div>
        {/*
        <div className="flex items-center gap-2">
          <div className="relative">
            <span className="flex h-3 w-3 rounded-full bg-green-500" />
            <span className="flex h-3 w-3 rounded-full bg-green-500 animate-ping absolute top-0" />
          </div>
          <p className="text-sm font-medium leading-none sm:hidden">Pending</p>
        </div>
        */}

        {/*<DropdownMenu>
          <DropdownMenuTrigger>
            <Dots className="w-4 h-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem className="text-red-500 focus:text-red-500">
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
  </DropdownMenu>*/}
      </div>

      <div className="mb-4 items-start pb-4 space-y-1 last:mb-0 last:pb-0">
        <div className="flex items-center gap-2 text-muted-foreground">
          <CalendarIcon className="w-4 h-4" />
          <p className="text-sm font-medium">{formatDate(property.start_date)} - {formatDate(property.end_date)}</p>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <MapPinIcon className="w-4 h-4" />
          <p className="text-sm font-medium">{property.address?.split(',')[0]}</p>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <DollarSignIcon className="w-4 h-4" />
          <p className="text-sm font-medium">
            <span className="text-muted-foreground font-extrabold">
              {property.price}
            </span>
            /month
          </p>
        </div>

      </div>
      {/*<div className="flex justify-between gap-3">
        <Button className="w-full gap-4">
          <CheckIcon className="ml-[-4px] mr-[-10px]" />
          Mark as Claimed
        </Button>

        <PropertyForm>
          <Button variant="secondary" className="w-full">
            Edit
          </Button>
        </PropertyForm>
</div>*/}
    </div>
  );
};

export default Property;
