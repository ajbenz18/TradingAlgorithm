# TradingAlgorithm
A simple stock trading algorithm using Alpaca broker API

This is not investment advice, and I advise against deploying this algorithm using real money, as it likely will lose your money. Rather, this should be treated as an example for the basic use of Alpaca (a comission free, API-based stock broker). More info can be found at https://alpaca.markets/

This algorithm incorporates a very simple strategy. When the first hourly candlestick fully forms above the 9 hour SMA line, we buy the stock. When the first candlestick fully forms below the line, we sell. We also check to make sure that the stock's 120 hour SMA line is above its 180 hour SMA line so that we are only trading stocks that are trending upwards.

Note that Alpaca does not provide hourly candlestick data, so I use their 15 minute candlestick data and rework it into hourly candlestick data.

The algorithm begins by connecting to your Alpaca brockerage account. It then looks at your first watchlist, and takes note of all the stocks that are in it. These are the stocks the algorithm will examine and trade with. The algorithm then gathers candlestick data about the stocks from Alpaca, and uses the logic above to determine what stocks to buy and sell.

The algorithm is intended to be run once an hour, every hour the market is open. I achieved this using AWS Lambda, and scheduled the algorithm to run using the cron expression: cron(30 9-15/1 ? * MON-FRI * ) with Cloudwatch Events.

If you intend to upload an Alpaca trading algorithm to AWS Lambda as I did, here are a few tips you may find helpful:

* Download all the dependencies into a local directory with your python script using ```pip3 install -t . packageName```
* (For MacOS and Windows users) The Alpaca python package uses pandas and numpy. After downloading this package locally, you need to open the folder and delete any folders pretaining to pandas and numpy. You will then need to replace them with the linux version, since AWS runs on Linux, and the windows/mac versions of numpy/pandas are not compatitable with it.
They can be found here: https://pypi.org/project/numpy/#files and here https://pypi.org/project/pandas/#files
I'm running Python 3.7, so I used numpy-1.19.0-cp37-cp37m-manylinux1_x86_64.whl and pandas-1.0.5-cp37-cp37m-manylinux1_x86_64.whl
Once you download these you will need to unzip them using ```$ unzip pandas-1.0.5-cp37-cp37m-manylinux1_x86_64.whl``` and ```$ unzip numpy-1.19.0-cp37-cp37m-manylinux1_x86_64.whl```
If you don't do this, you will get some funky error messages about how certain C-extensions of numpy are missing
* zip up all of these libraries and your python script and upload them to an Amazon S3 bucket (the .zip folder will likely be too large to upload to Lambda directly)
* If you haven't used AWS Lambd before, watch a python AWS Lambda tutorial video because ^that's^ not all you need to know.
