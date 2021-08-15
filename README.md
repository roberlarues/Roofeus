# Roofeus
Blender plugin to generate tiled geometry based on a template along a surface .

![Roofeus result](images/Result.png?raw=true "Roofeus result")

## Purpose
If you want to apply displacement maps in a plane in blender, you'll need more vertices inside the plane.
You can create them automatically with subdivisions:
![Subdivision comparison](images/SubdivisionComparison.png?raw=true "Subdivision comparison")
The more subdivisions you make, the more better results you'll have, but it will be more heavy and more complex to render.
And there are lot of useless geometry.

You can create them manually, but in extensive surfaces with lot of details could be a pain...

Roofeus offers another posibility for repetitive patterns:
1) Define a template over the texture (composed by vertices and faces)
2) Apply it in a blender face, adapting it to the face UVs

This solution allows to create subdivisions with the exact precision you will define in the template and very fast.
![Roofeus result comparison](images/ResultComparison.png?raw=true "Roofeus result comparison")
On the left, plane subdivided by blender using Multiresolution tool and 7 simple subdivisions (>16k vertices). 
On the right, roofeus result (916 vertices).

## How to install
To install roofeus add-on, compress the "roofeus" folder in a zip file and install it from the blender add-ons menu.
You can find more information about install blender add-ons in https://docs.blender.org/manual/en/latest/editors/preferences/addons.html

To run template_editor.py and main.py you will need python3 and the dependencies in requirements.txt

## How to use
Roofeus is intended to use in 2 steps: create the template and using it in blender.

### Create a template
To create and edit templates you can run the template_editor.py script to open the visual editor. It will allow you to:
- Open a texture to draw vertices over it
- Open an existing template
- Save the template (txt extension, for the moment)
- Create and edit vertices
- Create and edit faces

![Template editor](images/TemplateEditor.png?raw=true "Template editor")
  
In the "Face creation" tab, the texture and template is displayed in a 2x2 grid. That is because, when you apply it as a repetitive pattern in blender,
you'll want to have the vertices of your template linked to the next 'projected' template. So, you can create faces between them.

  
### Use a template
Select a face in the edit mode and open the "Roofeus" vertical tab. A panel with some options will be displayed:

![Blender panel](images/BlenderPanel.png?raw=true "Blender panel")
- Template: The created template to apply
- Fill uncompleted space: fills the vertices that were linked to other vertices in the template that doesn't fit in the
target face to the target vertices.
- Delete original vertex: deletes the target vertices after apply roofeus.
- Delete original face: deletes the target faces after apply roofeus.
- Roofeus: does the magic.
  
