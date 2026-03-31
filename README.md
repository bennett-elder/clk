# Summary

Clickup Client with an emphasis on the CLI.

Pronounce it click. Pronounce it clock. Pronounce it cluck. Pronounce it clack.

Whichever way, type it fast.

# Usage

```
clk add since last acme
clk add 1400 1530 dunder
clk add 10 min cust-2977
clk add 10m cust-2977
clk recent
clk bins
clk show-config
```

# Installation

If you skip this section the script will remind you.

## Private key

Please create a key for clickup at https://clickup.com/api/developer-portal/authentication#personal-token and set environment variable `CLICKUP_PK` to that value.

## Clickup Team ID

Your team id is the number after the base website domain.

```
https://app.clickup.com/YOUR_ID_HERE
```

Please set environment variable `CLICKUP_TEAM_ID` to that number.

## Homebrew

```
brew tap bennett-elder/honk
brew install clk
```