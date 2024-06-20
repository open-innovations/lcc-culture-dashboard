import lume from "lume/mod.ts";
import nunjucks from "lume/plugins/nunjucks.ts";	// Lume 2.0 requires us to add Nunjucks
import base_path from "lume/plugins/base_path.ts";
import date from "lume/plugins/date.ts";
import metas from "lume/plugins/metas.ts";
import postcss from "lume/plugins/postcss.ts";


// Importing the OI Lume charts and utilities
import oiViz from "https://deno.land/x/oi_lume_viz@v0.15.1/mod.ts";
import autoDependency from "https://deno.land/x/oi_lume_utils@v0.4.0/processors/auto-dependency.ts";
import csvLoader from "https://deno.land/x/oi_lume_utils@v0.4.0/loaders/csv-loader.ts";
import jsonLoader from "lume/core/loaders/json.ts";


const site = lume({
  src: './src',
  // TODO Update this with the proper URL
  location: new URL("https://open-innovations.github.io/lcc-culture-dashboard/"),
});



// Need to explicitly include it for Lume 2
site.use(nunjucks());


// The autodependency processor needs to be registered before the base path plugin,
// or else the autodepended paths will not be rewritten to include the path prefix
// set in location passed to the lume constructor (above)
site.process([".html"], (pages) => pages.forEach(autoDependency));

site.loadData([".csv", ".tsv", ".dat"], csvLoader({ basic: true }));
site.loadData([".geojson"], jsonLoader);
site.loadData([".hexjson"], jsonLoader);


// Import lume viz
import oiVizConfig from "./oi-viz-config.ts";
site.use(oiViz(oiVizConfig));

site.use(oiViz({
	assetPath: '/assets/oi',
	componentNamespace: 'oi.viz',
		"scales": {
			"lightcyan": 'rgb(255,255,255) 0%, hsl(173, 100%, 50%) 100%',
      "darkcyan": 'rgb(30, 172, 175) 0%, rgb(0, 69, 99) 100%',
      
		}
}));

site.use(base_path());
site.use(metas({
  defaultPageData: {
    title: 'Culture Dashboard', // Use the `date` value as fallback.
  },
}));
site.use(date());
site.use(postcss({}));

site.copy('CNAME');
site.copy('.nojekyll');
site.copy('assets/images');
site.copy('assets/css/fonts');

export default site;
