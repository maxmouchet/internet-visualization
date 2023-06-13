# internet-visualization

This repository contains the source code for the web interface demoed in "[Towards an interactive visualization of the Internet](https://www.youtube.com/watch?v=txp0P-ETWrQ)" ([slides](https://zenodo.org/record/8034723/files/TowardsAnInteractiveVisualizationOfTheInternet.pdf?download=1), [dataset](https://zenodo.org/record/8034723)).

![Screenshot](ui.png)

## Reproduce the web interface

To reproduce the web interface demoed in the talk, download the tileset (5.2GB) and start the server:
```bash
curl -Lo data/iris-2022-04-02.mbtiles 'https://zenodo.org/record/8034723/files/iris-2022-04-02.mbtiles?download=1'
docker compose up
```
Then, open http://localhost:1234 in your browser.

## Rebuild the dataset

We provide four data files:
- [`iris-2022-04-02.edges`](https://zenodo.org/record/8034723/files/iris-2022-04-02.edges.zst?download=1): the IP-level graph in the [LGL format](https://github.com/TheOpteProject/LGL#input-format-lgl)
- [`iris-2022-04-02.layout`](https://zenodo.org/record/8034723/files/iris-2022-04-02.layout.zst?download=1): the coordinates of each IP address as computed by the LGL algorithm
- [`iris-2022-04-02.geojsonl`](https://zenodo.org/record/8034723/files/iris-2022-04-02.geojsonl.zst?download=1): points and lines representing IP addresses and links, augmented with RIR and AS information
- [`iris-2022-04-02.mbtiles`](https://zenodo.org/record/8034723/files/iris-2022-04-02.mbtiles?download=1): the tileset used by Mapbox GL

In this section we show how to build the tileset starting from the IP-level graph.

If you want to run this on your own data, simply replace `iris-2022-04-02.edges` with your own file.
You can use the `write_lgl` function of [networkxtra](https://github.com/maxmouchet/networkxtra) to convert a graph to the LGL format. 

### Requirements

- [minilgl](https://github.com/maxmouchet/minilgl) for computing the layout
- [tippecanoe](https://github.com/mapbox/tippecanoe) for building the tilesets
- [Python](https://www.python.org) and [Poetry](https://github.com/python-poetry/poetry)

### Download the graph

```bash
curl -Lo data/iris-2022-04-02.edges.zst 'https://zenodo.org/record/8034723/files/iris-2022-04-02.edges.zst?download=1'
zstd -d data/iris-2022-04-02.edges.zst
```

### Compute the layout

```bash
lglayout2d -t 4 data/iris-2022-04-02.edges
mv lgl.out data/iris-2022-04-02.layout
```

With this graph containing 1.3M nodes and 3.5M edges this should take ~2 hours, depending on your machine and the number of threads set with `-t`.

### Build the GeoJSON file

Create a virtual environment for the `internet_maps` module and enter a shell inside it:

```bash
poetry -C python/ install
poetry -C python/ shell
```

Augment the graph with RIR and AS information, convert the node positions to the approriate coordinate system and output a GeoJSONL file:
```bash
internet-maps geojson --bgp-date 2022-04-02 --scale 10 \
    data/iris-2022-04-02.edges data/iris-2022-04-02.layout data/iris-2022-04-02.geojsonl
```

This is relatively fast, although downloading the BGP RIB can take some time.

### Build the tileset

We encode some metadata in the tileset name as a JSON string.

```bash
tippecanoe \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    --force \
    --hilbert \
    --maximum-zoom=g \
    --read-parallel \
    --name='{"data_source": "Iris", "vantage_point": "LIP6, Paris, France", "date": "2022-04-02"}' \
    --output data/iris-2022-04-02.mbtiles data/iris-2022-04-02.geojsonl 
```

This should take ~15 minutes depending on your machine.
