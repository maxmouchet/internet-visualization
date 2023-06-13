<template>
  <div></div>
</template>

<script lang="ts">
import maplibregl from "maplibre-gl";
import colorbrewer from "colorbrewer";
import {LayerSpecification, SourceSpecification} from "maplibre-gl/types/style-spec/types";

export default {
  props: ["tilesetUrl", "asFilter", "assignFilter", "orgFilter", "classificationFilter", "edgeColor", "bgColor"],
  mounted() {
    this.map = new maplibregl.Map({
      accessToken: "",
      container: this.$el,
      style: {
        version: 8,
        sources: {},
        glyphs: "http://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
        layers: [{
          id: "background",
          type: "background",
          paint: {"background-color": this.bgColor}
        }]
      },
      center: [0, 0],
      minZoom: 4,
      maxZoom: 16,
      zoom: 5,
    });
    this.map.addControl(new maplibregl.FullscreenControl());
    this.map.addControl(new maplibregl.NavigationControl({"showCompass": false}));
  },
  unmounted() {
    this.map.destroy();
  },
  methods: {
    updateFilter() {
      const filters = [];
      if (this.asFilter.length > 0) {
        filters.push(['any',
          ['match', ['get', 'u_as'], this.asFilter, true, false],
          ['match', ['get', 'v_as'], this.asFilter, true, false]
        ]);
      }
      if (this.assignFilter.length > 0) {
        filters.push(['any',
          ['match', ['get', 'u_assignment'], this.assignFilter, true, false],
          ['match', ['get', 'v_assignment'], this.assignFilter, true, false]
        ]);
      }
      if (this.orgFilter.length > 0) {
        filters.push(['any',
          ['match', ['get', 'u_organization'], this.orgFilter, true, false],
          ['match', ['get', 'v_organization'], this.orgFilter, true, false]
        ]);
      }
      if (this.classificationFilter.length > 0) {
        filters.push(['any',
          ['match', ['get', 'u_classification'], this.classificationFilter, true, false],
          ['match', ['get', 'v_classification'], this.classificationFilter, true, false]
        ]);
      }
      if (filters.length > 0) {
        this.map.setFilter(`${this.currentVectorLayer.id}-edges`, ['any', ...filters]);
      } else {
        this.map.setFilter(`${this.currentVectorLayer.id}-edges`, null);
      }
    }
  },
  watch: {
    async asFilter(values) {
      this.updateFilter();
    },
    async assignFilter(values) {
      this.updateFilter();
    },
    async orgFilter(values) {
      this.updateFilter();
    },
    async classificationFilter(values) {
      this.updateFilter();
    },
    async bgColor(value) {
      const style = this.map.getStyle();
      for (const layer of style.layers) {
        if (layer.id == "background") {
          layer.paint["background-color"] = value;
          break;
        }
      }
      this.map.setStyle(style);
    },
    async edgeColor(value) {
      let assignments = [];
      let prop = "";

      if (value == "Assignment") {
        assignments = ['AFRINIC', 'APNIC', 'ARIN', 'LACNIC', 'RIPE NCC'];
        prop = "u_assignment";
      } else {
        assignments = ['Computer and Information Technology', 'Service', 'Education and Research', 'Freight, Shipment, and Postal Services', 'Media, Publishing, and Broadcasting'];
        prop = "u_classification";
      }

      const colors = colorbrewer.Set2[assignments.length];
      const lineColor = ["match", ["get", prop]];
      console.log(colors);
      for (let i = 0; i < assignments.length; i++) {
        lineColor.push(assignments[i]);
        lineColor.push(colors[i]);
      }
      lineColor.push("white");
      this.map.setPaintProperty(`${this.currentVectorLayer.id}-edges`, "line-color", lineColor);
    },
    async tilesetUrl(newUrl, oldUrl) {
      const assignments = ['AFRINIC', 'APNIC', 'ARIN', 'LACNIC', 'RIPE NCC'];
      const colors = colorbrewer.Set2[assignments.length];
      const lineColor = ["match", ["get", "u_assignment"]];
      for (let i = 0; i < assignments.length; i++) {
        lineColor.push(assignments[i]);
        lineColor.push(colors[i]);
      }
      lineColor.push("white");

      const newTileset = await fetch(newUrl).then(response => response.json());
      const newVectorLayer = newTileset.vector_layers[0];

      const newSource: SourceSpecification = {
        type: "vector",
        tiles: newTileset.tiles,
        minzoom: newTileset.minzoom,
        maxzoom: newTileset.maxzoom
      };

      const newEdgeLayer: LayerSpecification = {
        id: `${newVectorLayer.id}-edges`,
        source: newTileset.name,
        "source-layer": newVectorLayer.id,
        filter: ["==", "$type", "LineString"],
        type: "line",
        paint: {
          "line-color": lineColor,
          "line-opacity": 0.0,
          "line-opacity-transition": {duration: 250},
          "line-width": 1,
        }
      };

      const newNodeLayer: LayerSpecification = {
        id: `${newVectorLayer.id}-nodes`,
        source: newTileset.name,
        "source-layer": newVectorLayer.id,
        filter: ["==", "$type", "Point"],
        type: "symbol",
        layout: {
          'icon-image': 'circle',
          'icon-size': 1,
          "text-field": ["concat", ["get", "title"], "\n", ["get", "as"]],
          'text-font': ['Open Sans Bold'],
          'text-offset': [0, 0.5],
          'text-anchor': 'top',
        },
        paint: {
          "text-color": "white"
        },
        minzoom: 11
      }

      if (this.map.getSource(newTileset.name) === undefined) {
        this.map.addSource(newTileset.name, newSource);
        this.map.addLayer(newEdgeLayer);
      }

      // TODO: From npm instead of src/.
      const imageUrl = new URL('icons/circle-stroked.png', import.meta.url);
      console.log(imageUrl)
      this.map.loadImage(
        imageUrl.href,
        (error, image) => {
          this.map.addImage('circle', image);
          this.map.addLayer(newNodeLayer);
        });

      if (oldUrl !== undefined) {
        const oldTileset = await fetch(oldUrl).then(response => response.json());
        const oldVectorLayer = oldTileset.vector_layers[0];
        const oldFilter = this.map.getFilter(`${oldVectorLayer.id}-edges`);
        this.map.setFilter(`${newVectorLayer.id}-edges`, oldFilter);
        this.map.setPaintProperty(`${oldVectorLayer.id}-edges`, "line-opacity", 0);
        setTimeout(() => {
          this.map.removeLayer(`${oldVectorLayer.id}-edges`);
          this.map.removeLayer(`${oldVectorLayer.id}-nodes`);
          this.map.removeSource(oldTileset.name);
        }, 250);
      }
      this.map.setPaintProperty(`${newVectorLayer.id}-edges`, "line-opacity", 0.5);
      this.currentVectorLayer = newVectorLayer;

      // TEMP
      const extraSource: SourceSpecification = {
        type: "geojson",
        data: {
          "type": "FeatureCollection",
          "features": [{
            "type": "Feature",
            "properties": {
              "title": "COMCAST-7922",
              "kind": "as_label",
              "asn": 7922,
              "organization": "Comcast Cable Communications, LLC",
              "assignment": "ARIN"
            },
            "geometry": {"type": "Point", "coordinates": [1.7889166412573787, 4.901252105046275]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "ATT-INTERNET4",
              "kind": "as_label",
              "asn": 7018,
              "organization": "AT&T Services, Inc.",
              "assignment": "AT&T Bell Laboratories"
            },
            "geometry": {"type": "Point", "coordinates": [-4.848264979517643, 1.1354844486115436]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "CHINANET-BACKBONE",
              "kind": "as_label",
              "asn": 4134,
              "organization": "China Telecom",
              "assignment": "APNIC"
            },
            "geometry": {"type": "Point", "coordinates": [-5.799688252230719, -3.9312614477677847]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "CHINA169-Backbone",
              "kind": "as_label",
              "asn": 4837,
              "organization": "CHINA UNICOM Industrial Internet Backbone",
              "assignment": "APNIC"
            },
            "geometry": {"type": "Point", "coordinates": [-4.422843747762918, -2.400059765881118]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "BT-UK-AS",
              "kind": "as_label",
              "asn": 2856,
              "organization": "British Telecommunications PLC",
              "assignment": "RIPE NCC"
            },
            "geometry": {"type": "Point", "coordinates": [7.922220658821364, 2.284620493817043]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "ASN-GammaTelecom",
              "kind": "as_label",
              "asn": 31655,
              "organization": "Gamma Telecom Holdings Ltd",
              "assignment": "RIPE NCC"
            },
            "geometry": {"type": "Point", "coordinates": [-1.6379351125883002, -7.420951777905607]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "CENTURYLINK-US-LEGACY-QWEST",
              "kind": "as_label",
              "asn": 209,
              "organization": "CenturyLink Communications, LLC",
              "assignment": "ARIN"
            },
            "geometry": {"type": "Point", "coordinates": [5.122397097064731, -1.8408489998940414]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "CHINAMOBILE-CN",
              "kind": "as_label",
              "asn": 9808,
              "organization": "China Mobile",
              "assignment": "APNIC"
            },
            "geometry": {"type": "Point", "coordinates": [-5.653172573739635, 1.12432635049086]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "KIXS-AS-KR",
              "kind": "as_label",
              "asn": 4766,
              "organization": "Korea Telecom",
              "assignment": "APNIC"
            },
            "geometry": {"type": "Point", "coordinates": [4.0018636085360395, -1.4031295114659432]}
          }, {
            "type": "Feature",
            "properties": {
              "title": "KDDI",
              "kind": "as_label",
              "asn": 2516,
              "organization": "KDDI CORPORATION",
              "assignment": "APNIC"
            },
            "geometry": {"type": "Point", "coordinates": [-3.212308773097353, 0.4665119224737128]}
          }]
        }
      }
      this.map.addSource("extra", extraSource);
      const lineColor2 = ["match", ["get", "assignment"]];
      for (let i = 0; i < assignments.length; i++) {
        lineColor2.push(assignments[i]);
        lineColor2.push(colors[i]);
      }
      lineColor2.push("white");
      const extraLayer: LayerSpecification = {
        id: "extra",
        source: "extra",
        type: "symbol",
        layout: {
          "text-field": ["get", "title"],
          "text-font": ["Open Sans Bold"],
          "text-size": 21,
          // "text-padding": 1,
          // "text-max-angle": 30,
          // "symbol-placement": "line",
          // "text-rotation-alignment": "map",
          // "text-pitch-alignment": "viewport"
        },
        paint: {
          "text-color": "white",
          "text-halo-blur": 1,
          "text-halo-color": "black",
          "text-halo-width": 1,
        }
      };
      this.map.addLayer(extraLayer);
      // TEMP

      // TODO: Load external GeoJSON with IXPs and other features location?
      // TODO: https://docs.mapbox.com/help/tutorials/show-changes-over-time/#add-a-time-slider

      // TODO: Option for showing only links where near/far AS are different.

      // TODO: Legend + info (zoom level)
      // TODO: Terrain, or at-least show RTT from source (color option? store cum RTT in edges).
      // TODO: Option to show edge RTT (between near and far).

      // if (this.map.getSource("default") === undefined) {
      //   this.map.addSource("default", source);
      // }
      //
      // for (const vl of tileset.vector_layers) {
      //   this.map.addLayer({
      //     id: vl.id,
      //     source: "default",
      //     "source-layer": vl.id,
      //     filter: ["==", "$type", "LineString"],
      //     type: "line",
      //     paint: {
      //       // TODO: Gradient?
      //       "line-color": lineColor,
      //       "line-opacity": 0.5,
      //       "line-width": 0.5
      //     }
      //   });
      // }
      //
      // const l1 = this.map.getLayer(tileset.vector_layers[0].id)
      // const l2 = this.map.getLayer(tileset.vector_layers[1].id)
      // if (l1.layout)

      // For layer 0, using name "0d596de1a9cf49b8ad1452da91633a58__cf3ec498480a4b2c91e80dad80e54ce7lglgeojsonl"
      // For layer 1, using name "0d4778eef3544f2ba4e64dac70f7167c__cf3ec498480a4b2c91e80dad80e54ce7lglgeojsonl"


      // const edgeLabelsLayer: LayerSpecification = {
      //   id: "edgeLabels",
      //   source: "default",
      //   // "source-layer": "",
      //   // "source-layer": tileset.vector_layers[0].id,
      //   filter: ["==", "$type", "LineString"],
      //   type: "symbol",
      //   minZoom: 10,
      //   layout: {
      //     "text-field": ["get", "u_organization"],
      //     "text-font": ["Open Sans Light"],
      //     "text-size": 12,
      //     "text-padding": 1,
      //     // "text-max-angle": 30,
      //     "symbol-placement": "line",
      //     "text-rotation-alignment": "map",
      //     "text-pitch-alignment": "viewport"
      //   },
      //   paint: {
      //     "text-color": "white",
      //     // TODO: text-halo
      //   }
      //   //   "line-color": lineColor,
      //   //   "line-opacity": 0.5,
      //   //   //   [
      //   //   //   "interpolate", ["linear"], ["zoom"],
      //   //   //   5, 0.1,
      //   //   //   10, 0.25
      //   //   // ],
      //   //   "line-width": 0.5
      //   // }
      // }


      // else {
      //   const defaultSource = this.map.getSource("default");
      //   defaultSource.setTiles(tileset.tiles);
      // }
      // this.map.addLayer(edgeLabelsLayer);

      // TODO: Proper popup with link info.
      // this.map.on('click', 'edges', (e) => {
      //   console.log(e.features);
      //   new maplibregl.Popup()
      //     .setLngLat(e.lngLat)
      //     .setHTML(e.features[0].properties.name)
      //     .addTo(this.map);
      // });

      // console.log(colorbrewer.schemeGroups.sequential);

      // lineColor.push("white");
      // console.log(lineColor);
      // const layer1: LayerSpecification = {
      //   id: "overlay-0",
      //   source: "overlay",
      //   "source-layer": tileset.vector_layers[0].id,
      //   filter: ["==", "$type", "LineString"],
      //   type: "line",
      //   paint: {
      //     "line-color": "blue",
      //     "line-opacity": [
      //       "interpolate", ["linear"], ["zoom"],
      //       5, 0.1,
      //       10, 0.25
      //     ],
      //     "line-width": 2
      //   }
      // }
      // const layer2: LayerSpecification = {
      //   id: "overlay-1",
      //   source: "overlay",
      //   "source-layer": tileset.vector_layers[0].id,
      //   filter: ["==", "$type", "Point"],
      //   type: "symbol",
      //   layout: {
      //     "text-field": ["concat", ["get", "title"], "\n", ["get", "as"]],
      //     'text-font': [
      //       'Open Sans Bold'
      //     ],
      //     'text-offset': [0, 1.25],
      //     'text-anchor': 'top',
      //   },
      //   paint: {
      //     "text-color": "white"
      //   },
      //   minzoom: 12,
      // }
      // if (this.map.getLayer("overlay-0") != undefined) {
      //   this.map.removeLayer("overlay-0");
      // }
      // if (this.map.getLayer("overlay-1") != undefined) {
      //   this.map.removeLayer("overlay-1");
      // }
      // if (this.map.getSource("overlay") != undefined) {
      //   this.map.removeSource("overlay");
      // }
      // this.map.addSource("overlay", source);
      // this.map.addLayer(layer1);
      // this.map.addLayer(layer2);
    }
  }
}
</script>
