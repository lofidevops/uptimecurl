# uptimecurl

Simple monitoring tool designed for rapid deployment and results.

## Sample report

```
uptimecurl --sample
xdg-open result.html
```

The sample report performs:

* a simple HTTP request from `en.wikipedia.org:80`
* a port check on `en.wikipedia.org:443`

Expected results:

* HTTP request fails due to a 301 redirect (expecting 200 OK)
* port check succeeds (HTTPS port is available)

## Sharing

uptimecurl  
Copyright 2020 David Seaward  
SPDX-License-Identifier: GPL-3.0-or-later  
