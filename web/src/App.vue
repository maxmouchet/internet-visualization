<template>
  <div id="app-root" class="vh-100 vw-100">
    <aside id="sidebar" class="d-flex flex-column h-100">
      <div class="container-fluid text-light">
        <h5 class="mt-2">Data source</h5>
        <form>
          <div class="form-group">
            <label for="select-data-source">Measurement platform</label>
            <v-select id="select-data-source" placeholder="Loading..." :clearable="false" :options="dataSources" v-model="selectedDataSource"/>
          </div>
          <div class="form-group">
            <label for="select-vantage-point">Vantage point</label>
            <v-select id="select-vantage-point" placeholder="Loading..." :clearable="false" :options="vantagePoints"
                      v-model="selectedVantagePoint"/>
          </div>
          <div class="form-group">
            <label for="select-date">Date</label>
            <v-select id="select-date"  placeholder="Loading..." :clearable="false" :options="dates"
                      v-model="selectedDate"/>
          </div>
          <div class="my-3"/>
          <h5>Filters</h5>
          <div class="form-group">
            <label for="select-filter-assign">Assignment (IANA)</label>
            <v-select id="select-filter-assign" multiple placeholder="All"
                      :options="['AFRINIC', 'ARIN', 'APNIC', 'LACNIC', 'RIPE NCC']" v-model="selectedAssign"/>
          </div>
          <div class="form-group">
            <label for="select-filter-as">Autonomous system</label>
            <v-select id="select-filter-as" multiple placeholder="All" :options="asList" :filterable="false"
                      @search="onAsSearch" v-model="selectedAs"/>
          </div>
          <div class="form-group">
            <label for="select-filter-org">Organization</label>
            <v-select id="select-filter-org" multiple placeholder="All" :options="orgList" :filterable="false"
                      @search="onOrgSearch" v-model="selectedOrg"/>
          </div>
          <div class="form-group">
            <label for="select-filter-classification">Classification</label>
            <v-select id="select-filter-classification" multiple placeholder="All" :options="['Finance and Insurance', 'Media, Publishing, and Broadcasting', 'Service', 'Agriculture, Mining, and Refineries (Farming, Greenhouses, Mining, Forestry, and Animal Farming)', 'Manufacturing', 'Museums, Libraries, and Entertainment', 'Community Groups and Nonprofits', 'Health Care Services', 'Freight, Shipment, and Postal Services', 'Utilities (Excluding Internet Service)', 'Computer and Information Technology', 'Travel and Accommodation', 'Government and Public Administration', 'Construction and Real Estate', 'Retail Stores, Wholesale, and E-commerce Sites', 'Other', 'Education and Research']" v-model="selectedClassification"/>
          </div>
          <div class="my-3"/>
          <h5>Style</h5>
          <div class="form-group">
            <label for="select-style-bg-color">Background color</label><br/>
            <input id="select-style-bg-color" type="color" v-model="selectedBgColor">
          </div>
          <div class="form-group">
            <label for="select-style-edge-color">Edge color</label>
            <v-select id="select-style-edge-color" :clearable="false"
                      :options="['Assignment', 'Classification']" v-model="selectedEdgeColor"/>
          </div>
<!--          <div class="form-group">-->
<!--            <label for="select-style-edge-opacity">Edge opacity</label>-->
<!--            <input id="select-style-edge-opacity" type="range" min="0" max="1" step="0.01" value="0.25">-->
<!--          </div>-->
<!--          <div class="form-group">-->
<!--            <label for="select-style-edge-size">Edge size</label>-->
<!--            <input id="select-style-edge-size" type="range" min="0" max="5" step="0.1" value="0.5">-->
<!--          </div>-->
        </form>
      </div>
    </aside>
    <mapgl id="map" :tileset-url="tilesetUrl" :asFilter="selectedAs" :assignFilter="selectedAssign" :bgColor="selectedBgColor" :edgeColor="selectedEdgeColor"
           :orgFilter="selectedOrg" :classificationFilter="selectedClassification"></mapgl>
  </div>
</template>

<script lang="ts">
import {debounce} from "lodash";
import MapGL from "./MapGL.vue";
import vSelect from "vue-select";

export default {
  components: {
    mapgl: MapGL,
    "v-select": vSelect
  },
  methods: {
    // TODO: Refactor
    onAsSearch(search, loading) {
      if (search.length) {
        loading(true);
        this.asSearch(loading, search, this);
      }
    },
    asSearch: debounce((loading, search, vm) => {
      fetch(
        `http://localhost:8001/as?q=${escape(search)}`
      ).then(res => {
        res.json().then(json => (vm.asList = json));
        loading(false);
      });
    }, 350),
    onOrgSearch(search, loading) {
      if (search.length) {
        loading(true);
        this.orgSearch(loading, search, this);
      }
    },
    orgSearch: debounce((loading, search, vm) => {
      fetch(
        `http://localhost:8001/orgs?q=${escape(search)}`
      ).then(res => {
        res.json().then(json => (vm.orgList = json));
        loading(false);
      });
    }, 350)
  },
  data() {
    return {
      asList: [],
      orgList: [],
      selectedAs: [],
      selectedAssign: [],
      selectedOrg: [],
      selectedClassification: [],
      // selectedBgColor: "#FFFFE0",
      selectedBgColor: "#000000",
      selectedEdgeColor: "Assignment",
      selectedDataSource: null,
      selectedVantagePoint: null,
      selectedDate: null,
      tilesets: {} as { [vantagePoint: string]: { [date: string]: string } }
    };
  },
  computed: {
    dataSources() {
      return Object.keys(this.tilesets)
        .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    },
    vantagePoints() {
      if (this.selectedDataSource in this.tilesets) {
        return Object.keys(this.tilesets[this.selectedDataSource])
          .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
      }
      return []
    },
    dates() {
      if (this.selectedDataSource in this.tilesets
        && this.selectedVantagePoint in this.tilesets[this.selectedDataSource]) {
        // TODO: Sort dates.
        return Object.keys(this.tilesets[this.selectedDataSource][this.selectedVantagePoint]).sort();
      }
      return []
    },
    tilesetUrl() {
      return this.tilesets?.[this.selectedDataSource]?.[this.selectedVantagePoint]?.[this.selectedDate];
    }
  },
  async created() {
    // TODO: Toast notification on error?
    const response = await fetch("http://localhost:8000/services");
    const tilesets = await response.json();
    for (const tileset of tilesets) {
      const meta = JSON.parse(tileset.name)
      if (!(meta.data_source in this.tilesets)) {
        this.tilesets[meta.data_source] = {}
      }
      if (!(meta.vantage_point in this.tilesets[meta.data_source])) {
        this.tilesets[meta.data_source][meta.vantage_point] = {}
      }
      this.tilesets[meta.data_source][meta.vantage_point][meta.date] = tileset.url
    }
    this.selectedDataSource = this.dataSources[0]
    this.selectedVantagePoint = this.vantagePoints[0]
    this.selectedDate = this.dates[0]
  },
};
</script>

<style scoped>
@import "https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@400;700&display=swap";
@import "npm:bootstrap/dist/css/bootstrap.min.css";
@import "npm:maplibre-gl/dist/maplibre-gl.css";
@import "npm:vue-select/dist/vue-select.css";

#app-root {
  display: grid;
  grid-template-columns: 1fr 5fr;
  grid-template-rows: auto;
}

#title {
  font-family: "Aref Ruqaa", serif;
}

#sidebar {
  background-color: black;
  grid-column: 1;
  grid-row: 1;
  z-index: 1;
}

#map {
  /*grid-column: 1/3;*/
  grid-column: 2/3;
  grid-row: 1;
}

>>> {
  --vs-controls-color: #fff;
  --vs-border-color: #664cc3;

  --vs-dropdown-bg: #282c34;
  --vs-dropdown-color: #cc99cd;
  --vs-dropdown-option-color: #cc99cd;

  --vs-selected-bg: #664cc3;
  --vs-selected-color: #eeeeee;

  --vs-search-input-color: #eeeeee;

  --vs-dropdown-option--active-bg: #664cc3;
  --vs-dropdown-option--active-color: #eeeeee;
}
</style>
