# LeetCodeFetcher
Here is a LeetCode submission fetching and saving tool.

You need to get your own LeetCode website cookie (You may get it from a network requests inspector) and put it in the `cookie` param on the top of the python file. 

Running this python file will automatically fetch your LeetCode submissions and save all AC ones. You may change the code a little bit to automatically add, commit, and push them to GitHub. Just uncomment the bottom part of `handleProblem` function.

At the meantime, this program offers the function of generating a TOC file, containing links to all the codes you saved before. To apply this usage, you need to assign the `tocPrefix` param.

The `sid` file it created is used to rule out of the formerly finished codes. Never mind about it.