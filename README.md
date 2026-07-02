<p align="center">
  <img src="assets/android-chrome-512x512.png" alt="NBT Library Logo" width="100" height="100">
</p>

<h1 align="center">Media Ratings</h1>

<p align="center">
    A website to track, arrange and display my ratings and reviews of various pieces of media.
</p>

<p align="center">
  <a href="https://kadthehunter.github.io/Media-Ratings/">Visit the Website</a>
</p>

---

## About

Media Ratings is my very over-engineered website to display my ratings and reviews of various pieces of media.

- **Media:** Movies, TV Shows, Anime, Music, Videogames, and Books.
- **Sorting:** Divided into tiers of S, A, B, C, D, F and Unranked, with additional sorting automatically applied based on decimal rating, weight, and watched date (where applicable).
- **Automation:** Movies, TV Shows and Anime are automatically imported from Jellyfin, posters are automatically processed and inserted when provided, and manual categories such as Music, Videogames, and Books are automatically alphabetized in data.yml
- **Over-engineered:** [card.js](card.js) creates cards dynamically, arranges and sorts them by the relevant criteria, marks only images _outside_ the initial view for lazy loading, smartly collapses tiers when performing searches, supplements the review modal animation, and provides all the useful features of the site

---

## Why is this not part of Shouting into the Void?

Mainly because it couldn't really be achieved within the confines of the Minimal-Mistakes Jekyll theme (or any Jekyll theme really), at least not without substantial effort, and I am an incredibly lazy individual.

Even just frankensteining this code into the existing site would have been too much work, so I chose to simply make it a separate site.

---

## Disclaimer

Large portions of the HTML, CSS, JavaScript and Python were written by AI; That being said, I do not consider it to be "vibe-coding", because:
1. It frequently made mistakes that even I (with my limited knowledge) recognized and had to fix
2. Everything was my vision/design, except for the Back to Top button. I knew _exactly_ how I wanted this site to look and function, I just didn't have the specific knowledge to do it myself.
3. I do have _some_ experience programming, both in general and regarding web-dev, so I am at least aware of the risks of using AI, and I don't just blindly use code it provides.