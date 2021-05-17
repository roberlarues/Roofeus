# Roofeus
Blender plugin to generate tiled geometry along a surface based on a template.

## The problem
I was modeling my village in Blender to put it into Unreal Engine and make a game.
When I had to model the roofs, I decided to do it with displacement maps because i
wanted them realistic but efficient (handling LODs in Unreal).

Displacement map requires some geometry in the surface to work well. Starting from
a 4-corner plane model for the roof, I tried to make a grid subdivision, but the results
with the displacement map were not satisfactory: some triangles not desired, lots of subdivisions
 to acceptable results...

After that, i decided to cut by-hand the plane, exactly where i needed. This results were far better,
and using few inner polygons. The problem: it will be a pain made it manually for every roof of the village.

Roofeus borns as a solution to automatize this process.

## The solution
TODO

## How to use
TODO