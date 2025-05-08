# Leeds City Council Culture Dashboard

This is a repository for the Leeds City Council Culture Dashboard

You may need to customise some things to get started:

* Review the contents of `_config.ts`. Pay particular attention to the site URL,
  as this will affect how relative links are created. You can probably ignore
  the rest of this for the moment.
* The source for the site is held in the `src` directory.
* Review the contents of `src/_data.yml`
    * This is where the default page layout is defined in the `layout` key.
      The default is `templates/page.njk`. This template can be found in the
      `_includes` directory.
    * Edit the site title and other SEO metadata in  under the
      `metas` key. See the [Lume metas plugin documentation](https://lume.land/plugins/metas/)
      for more information.
* Edit the title of this page in the frontmatter above. You can override the
  template by setting the `layout` key. 

## Deploying a GitHub site

The page is set up 
https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow
