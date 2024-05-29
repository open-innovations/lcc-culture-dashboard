import lume from "lume/mod.ts";
import nunjucks from "lume/plugins/nunjucks.ts";	// Lume 2.0 requires us to add Nunjucks
import base_path from "lume/plugins/base_path.ts";
import date from "lume/plugins/date.ts";
import metas from "lume/plugins/metas.ts";
import postcss from "lume/plugins/postcss.ts";

const site = lume({
  src: './src',
  // TODO Update this with the proper URL
  location: new URL("https://open-innovations.github.io/lcc-culture-dashboard/"),
});






site.use(nunjucks()); // For Lume 2
site.use(base_path());
site.use(metas({
  defaultPageData: {
    title: 'title', // Use the `date` value as fallback.
  },
}));
site.use(date());
site.use(postcss({}));

site.copy('CNAME');
site.copy('.nojekyll');

export default site;
