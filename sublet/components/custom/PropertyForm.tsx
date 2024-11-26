"use client"

import { fetchAmenities, createProperty, createPropertyImage, fetchProperties } from "@/services/propertyService"

import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { ChangeEvent } from "react";
//import { useToast } from "@/components/ui/use-toast"

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

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label";
import { CalendarIcon, ImageIcon } from "@radix-ui/react-icons";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Calendar } from "../ui/calendar";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Textarea } from "../ui/textarea";
import { useEffect, useState } from "react"
import { ToggleGroup, ToggleGroupItem } from "../ui/toggle-group"
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar"

import Image from 'next/image'
import { AspectRatio } from "../ui/aspect-ratio"
import { Skeleton } from "../ui/skeleton"

const uriRegex = new RegExp('^(https?:\/\/)(localhost|[\da-z\.-]+)\.([a-z\.]{2,6}|[0-9]{1,5})([\/\w \.-]*)*\/?$');

const decimalRegex = /^-?\d+(\.\d)?$/;

const MAX_UPLOAD_SIZE = 1024 * 1024 * 3; // 3MB for each file
const ACCEPTED_FILE_TYPES = ['image/jpeg', 'image/png']; // Accepted image formats
const MAX_FILES = 6; // Maximum number of images

const formSchema = z.object({
  amenities: z.array(z.string().max(255)),
  title: z.string().max(255),
  address: z.string().max(255),
  beds: z.preprocess((value) => {
    // If value is already a number, return it
    if (typeof value === 'number') return value;
    // If it's a string, attempt to parse it
    if (typeof value === 'string') return parseFloat(value);
  }, z.number().int().min(0).max(2147483647)),
  baths: z.union([
    z.string().regex(decimalRegex).optional().transform((val) => val !== undefined ? parseFloat(val) : undefined),
    z.number().min(0).max(100).optional()
  ]).refine((val) => val === undefined || (typeof val === 'number' && val >= 0 && val <= 100 && decimalRegex.test(val.toString())), {
    message: "Baths must be a decimal with at most one decimal place and within the range -100 to 100."
  }),
  description: z.string().optional(),
  external_link: z.string().regex(uriRegex).max(255),
  price: z.preprocess((value) => {
    // If value is already a number, return it
    if (typeof value === 'number') return value;
    // If it's a string, attempt to parse it
    if (typeof value === 'string') return parseFloat(value);
  }, z.number().int().min(-2147483648).max(2147483647)),
  negotiable: z.boolean().optional(),
  start_date: z.date(),
  end_date: z.date(),
  expires_at: z.date(),
  images: z.array(z.instanceof(File)) // An array of File instances
    .refine((files) => files.length <= MAX_FILES, { message: `You can upload a maximum of ${MAX_FILES} images.` }) // Limit the number of files
    .refine((files) => files.every(file => file.size <= MAX_UPLOAD_SIZE), { message: `Each file must be less than ${MAX_UPLOAD_SIZE / (1024 * 1024)}MB.` }) // Check size for each file
    .refine((files) => files.every(file => ACCEPTED_FILE_TYPES.includes(file.type)), { message: 'Only JPEG and PNG files are accepted.' }), // Check type for each file
});

function getImageData(event: ChangeEvent<HTMLInputElement>) {
  // FileList is immutable, so we need to create a new one
  const dataTransfer = new DataTransfer();

  // Add newly uploaded images
  Array.from(event.target.files!).forEach((image) =>
    dataTransfer.items.add(image)
  );

  const files = dataTransfer.files;
  const displayUrl = URL.createObjectURL(event.target.files![0]);

  return { files, displayUrl };
}

interface PropertyFormProps {
  onNewProperty: any;
  children: React.ReactNode;
}

const PropertyForm = ({ onNewProperty, children }: PropertyFormProps) => {

  //const { toast } = useToast();
  const [amenities, setAmenities] = useState<string[]>([]);
  const [preview, setPreview] = useState("");

  /*useEffect(() => {
    fetchAmenities()
      .then((data) => {
        setAmenities(data);
      })
      .catch((error) => {
        console.error("Error fetching properties:", error);
      });
  }, []);*/

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      amenities: [],
      title: "",
      address: "",
      beds: 0,
      baths: 0,
      description: "",
      external_link: "",
      price: 0,
      negotiable: false,
      start_date: undefined,
      end_date: undefined,
      expires_at: undefined,
      images: [],
    },
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Assuming values contains an 'images' property along with other properties
    const { images, ...rest } = values;

    console.log(images);

    // Now, 'images' is a separate variable containing the images array
    // and 'rest' contains the rest of the properties from 'values'

    const property = {
      ...rest, // Spread the rest of the properties here
      start_date: format(rest.start_date, "yyyy-MM-dd") as string,
      end_date: format(rest.end_date, "yyyy-MM-dd") as string,
      expires_at: format(rest.expires_at, "yyyy-MM-dd'T'HH:mm:ssxxx") as string,
      baths: rest.baths!.toString(),
    };

    console.log(JSON.stringify(property));

    createProperty(property)
      .then((data) => {
        const subletId = data.id;
        console.log(subletId);

        const imageUploadPromises = images.reduce((promiseChain, image) => {
          return promiseChain.then(() => createPropertyImage(subletId, image)
            .then((data) => {
              console.log("return: " + data);
            })
            .catch((error) => {
              console.error('An error occurred during image upload:', error);
            })
          );
        }, Promise.resolve());
        imageUploadPromises
          .then(() => {
            console.log('All images have been uploaded successfully.');
            return subletId;
          })
          .catch((error) => {
            console.error('An error occurred during image upload:', error);
          });
      })
      .then((subletId) => {
        // Images have been uploaded, now fetch properties
        fetchProperties()
          .then((data) => {
            onNewProperty(data);
          })
          .catch((error) => {
            console.error("Error fetching properties:", error);
          });
      })
      .catch((error) => {
        console.error("Error in property creation or image upload:", error);
      });
  }

  return (
    <div>
      <Sheet>
        <SheetTrigger asChild>
          {children}
        </SheetTrigger>
        <SheetContent className="space-y-4 overflow-y-scroll">
          <SheetHeader>
            <SheetTitle className="text-2xl">New Listing</SheetTitle>
            <SheetDescription>
              Create a new property listing below. Make sure to fill in all required fields.
            </SheetDescription>
          </SheetHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              <FormField
                control={form.control}
                name="images"
                render={({ field: { onChange, value, ...rest } }) => (
                  <>
                    <FormItem className="py-2 space-y-1">
                      <FormControl>
                        <div className="relative rounded-xl overflow-hidden select-none">
                          <AspectRatio ratio={16 / 9} className="z-10">
                            {preview ?
                              <Image
                                src={preview}
                                alt="Preview"
                                objectFit="cover"
                                fill
                              />
                              :
                              <Skeleton className="h-full flex items-center justify-center">
                                <ImageIcon className="w-6 h-6" />
                              </Skeleton>
                            }

                          </AspectRatio>
                          <Input
                            type="file"
                            className="z-40 absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            {...rest}
                            onChange={(event) => {
                              const { files, displayUrl } = getImageData(event)
                              setPreview(displayUrl);
                              onChange([...value, ...Array.from(files).slice(0, 6 - value.length)]);
                            }}
                            multiple
                          />
                        </div>
                      </FormControl>
                      <FormDescription>
                        Select up to 6 images.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  </>
                )}
              />
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="title" className="text-right pr-3">Name</FormLabel>
                    <FormControl className="col-span-3">
                      <Input placeholder="ex. Chestnut 2bed 2ba" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="address" className="text-right pr-3">Address</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="string" placeholder="123 Main St, Philadelphia, PA 19104" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="price"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="price" className="text-right pr-3">Price</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="negotiable"
                render={({ field }) => (
                  <FormItem className="flex justify-end items-center gap-1">
                    <div className="flex gap-2">
                      <FormControl className="">
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <FormLabel htmlFor="negotiable" className="text-right col-start-3">
                        Negotiable?
                      </FormLabel>
                    </div>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="external_link"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="external_link" className="text-right pr-3">Link</FormLabel>
                    <FormControl className="col-span-3">
                      <Input placeholder="https://example.com" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 items-center gap-1 justify-start items-start pb-5">
                <FormField
                  control={form.control}
                  name="beds"
                  render={({ field }) => (
                    <FormItem className="grid grid-cols-2 items-center gap-1">
                      <FormLabel htmlFor="beds" className="text-right pr-3">Beds</FormLabel>
                      <FormControl className="col-span-1">
                        <Input type="number" {...field} />
                      </FormControl>

                      {/*<FormMessage className="col-span-4 text-right" />*/}
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="baths"
                  render={({ field }) => (
                    <FormItem className="grid grid-cols-2 items-center  gap-1">
                      <FormLabel htmlFor="baths" className="text-right pr-3">Baths</FormLabel>
                      <FormControl className="col-span-1">
                        <Input type="number" {...field} />
                      </FormControl>

                      {/*<FormMessage className="col-span-4 text-right" />*/}
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="start_date" className="text-right pr-3">Start Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild className="">
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Pick a date</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={new Date(field.value)}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            date < new Date() || date > form.getValues("end_date")!
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="end_date" className="text-right pr-3">End Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Pick a date</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={new Date(field.value)}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            (form.getValues("start_date") ? date < new Date(form.getValues("start_date")) : date < new Date()) || date < form.getValues("expires_at")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="expires_at"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1 pb-5">
                    <FormLabel htmlFor="expires_at" className="text-right pr-3">Expires At</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild className="">
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Pick a date</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={new Date(field.value)}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            date < new Date() || date > form.getValues("end_date")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="amenities"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1 pb-5">
                    <FormLabel htmlFor="amenities" className="text-right pr-3">Amenities</FormLabel>
                    <FormControl className="col-span-3">
                      <ToggleGroup
                        type="multiple"
                        className="flex flex-wrap justify-start gap-2"
                      >
                        {amenities.map((amenity, id) => (
                          <ToggleGroupItem
                            key={id}
                            value={amenity}
                            data-state={field.value?.includes(amenity) ? "on" : "off"}
                            aria-label="Toggle bold"
                            className="border"
                            onClick={() => {
                              const currentAmenities = field.value || [];
                              const updatedAmenities = currentAmenities.includes(amenity)
                                ? currentAmenities.filter(a => a !== amenity)  // Remove the amenity if it was selected
                                : [...currentAmenities, amenity];  // Add the amenity if it was not selected

                              field.onChange(updatedAmenities);  // Update the form field's value
                            }}
                          >
                            <Label className="p-0">
                              {amenity}
                            </Label>
                          </ToggleGroupItem>
                        ))}
                      </ToggleGroup>
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="description" className="text-right pr-3">Description</FormLabel>
                    <FormControl className="col-span-3">
                      <Textarea placeholder="Add features or descriptors..." {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              {/*<Button onClick={() => {
                console.log(form.getValues())
                //console.log("Start Date:", format(form.getValues("start_date"), "yyyy-MM-dd"));
                //console.log("End Date:", format(form.getValues("end_date"), "yyyy-MM-dd"));
                console.log(form.getFieldState("external_link"))
                //console.log(form.getFieldState("end_date"))
              }}>
                console log
            </Button>*/}

              <SheetFooter className="max-sm:flex max-sm: max-sm:gap-2 py-5">
                <SheetClose asChild>
                  <Button variant="secondary">Close</Button>
                </SheetClose>
                <Button type="submit">Save</Button>
              </SheetFooter>

            </form>
          </Form>
        </SheetContent>
      </Sheet >
    </div >
  )
}

export default PropertyForm