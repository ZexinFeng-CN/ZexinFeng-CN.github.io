# Project pages

Each project page lives in its own directory and is published as a static page by GitHub Pages:

- `works/copper-policy/index.html` → `/works/copper-policy/`
- Add another project under `works/<slug>/index.html` → `/works/<slug>/`

Keep each page's assets inside its project directory and use relative asset paths so the page works under its nested URL. Only copy files required by the public page; source recordings and other large development files should remain outside the deployed site.
