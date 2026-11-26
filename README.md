# The World Today — Thursday 26 November 2026 in one image

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/Rizaltri13/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/Rizaltri13/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

Entry for the [make.fun](https://make.fun) bounty
[**news-image-20261126: Sum up 26 November's world news in one
image**](https://make.fun/bounty/news-image-20261126).

A Python 3.13 program (standard library only, no network) that draws a
newspaper front page — masthead, hero story, six more stories and a news
ticker — and writes one 1024x1024 PNG to `/output/entry.png`.

## The day's news

- **Hero: 13 dead, 13 still trapped below.** Rescuers resumed the search
  on Thursday for 13 miners still trapped in a flooded illegal gold shaft
  in Bogor, West Java, after 13 bodies were recovered — six now
  identified. (Reuters)
- **Asia bounces back.** Nikkei +1.6%, Kospi +1.9% on Thursday after Wall
  Street fought back; Nvidia fell 3.9% to $149.30; Brent $94.81.
  (Reuters)
- **Seoul hikes to 3.25%.** Bank of Korea resumes tightening with a
  quarter-point rise as a chip export boom keeps inflation high. (Reuters)
- **China firms press Japan.** A JETRO survey finds Chinese rivals a
  growing threat to Japanese firms operating abroad. (Reuters)
- **Saudi hits back at Ras Isa.** Riyadh struck the Houthi-held Ras Isa
  refinery after attacks on Ras Tanura pushed oil near $95.
  (Arirang / Reuters)
- **Uber names Asia chief.** Rakesh Ranjan will lead India and South Asia
  from 4 January 2027. (Reuters)
- **Iowa blast a success.** The US Army says the controlled detonation of
  its bomb-chemical stockpile went exactly as planned. (AP)

## Run it

```sh
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Deterministic: running it twice writes byte-identical PNGs. No network
access; the hero photograph is bundled in this repo as `hero.png`.

## License

MIT — see [LICENSE](LICENSE).
