#!/usr/bin/env python3

import re

from colorsys import hsv_to_rgb
from PIL import Image, ImageDraw
from sys import argv

def build_frame(groups):
  return {
    'name': groups[0],
    'type': groups[1],
    'attributes': {},
    'children': []
  }

def build_structure(filename):
  open_exp = re.compile('^[ ]*object (.*): (.*)\n$')
  close_exp = re.compile('^[ ]*end\n$')
  attribute_exp = re.compile('^[ ]*(.*) = (.*)\n$')

  with open(filename, 'r') as f:
    lines = f.readlines()

    stack = [{'children': []}]

    for line in lines:
      open_match = open_exp.match(line)
      if open_match:
        child = build_frame(open_match.groups())
        stack[-1]['children'].append(child)
        stack.append(child)
        continue

      close_match = close_exp.match(line)
      if close_match:
        stack.pop()
        continue

      attribute_match = attribute_exp.match(line)
      if attribute_match:
        groups = attribute_match.groups()
        stack[-1]['attributes'][groups[0]] = groups[1]
        continue

  return stack[0]['children'][0]

def first_in(d, *args):
  for arg in args:
    if arg in d:
      return d[arg]

  return None

def extract_dimensions(attributes):
  left = attributes.get('Left')
  if left == None:
    return None

  top = attributes.get('Top')
  if top == None:
    return None

  width = first_in(attributes, 'ClientWidth', 'Width')
  if width == None:
    return None

  height = first_in(attributes, 'ClientHeight', 'Height')
  if height == None:
    return None

  return [int(left), int(top), int(left + width), int(top + height)]

def plumb(node, depth=0, breadth=0):
  depth += 1

  if len(node['children']) == 0:
    return (depth, breadth)

  breadth = max(breadth, len(node['children']))
  depth = max(plumb(c, depth, breadth)[0] for c in node['children'])

  return (depth, breadth)

def layout(node):
  max_depth, max_breadth = plumb(node)
  hue_coarse = 360.0 / float(max_depth + 1)
  hue_fine = hue_coarse / float(max_breadth + 1)

  def layout_recursive(node, draw, depth=0, index=0):
    dimensions = extract_dimensions(node['attributes'])
    if dimensions:
      hue = ((hue_coarse * depth) + (hue_fine * index)) / 360.0
      rgb = [int(x * 255.0) for x in hsv_to_rgb(hue, 1.0, 0.8)]
      draw.rectangle(dimensions, fill=tuple(rgb), outline=(0, 0, 0))

    for index, child in enumerate(node['children']):
      layout_recursive(child, draw, depth + 1, index)

  width = int(structure['attributes']['ClientWidth'])
  height = int(structure['attributes']['ClientHeight'])
  image = Image.new('RGB', (width, height), (255, 255, 255))
  draw = ImageDraw.Draw(image)
  layout_recursive(node, draw)
  return image

if len(argv) < 3:
  exit()

structure = build_structure(argv[1])

image = layout(structure)
image.save(argv[2])