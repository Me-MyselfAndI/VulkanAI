import { config } from "dotenv"
config();

import { Configuration, OpenAIApi } from "openai";
import readline from "readline";

const openAI = new OpenAIApi(new Configuration({
  apiKey: process.env.API_KEY
}));

const userInterface = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

import fs from "fs";

userInterface.prompt();
console.log("Type anything to get a response from the file");
userInterface.on("line", async input => {
  const html = fs.readFileSync('./page_source.html', "utf-8");

  const regex = {
    'src': /src=(\\)?(("(.)+?")|('(.)+?'))/gi,
    'href': /href=(\\|^=)?(("(.)+?")|('(.)+?'))/gi,
    'class': /class=(\\)?(("(.)+?")|('(.)+?'))/gi,
    'id': /id=(\\)?(("(.)+?")|('(.)+?'))/gi,
    'script': /<script\b[\s\S]*?<\/script>/gi,
    'svg': /<svg\b[\s\S]*?<\/svg>/gi,
    'meta': /<meta(.)+?>/gi,
    'style': /<style\b[\s\S]*?<\/style>/gi,
    // 'p': /<p\b[\s\S]*?<\/p>/gi,
  };

  let replacementTagAssigners = {
    'src': num => 'SRC' + num,
    'href': num => 'HREF' + num,
    'class': num => 'CLASS' + num,
    'id': num => 'ID' + num,
    'script': num => 'SCRIPT' + num,
    'svg': num => 'SVG' + num,
    'meta': num => 'META' + num,
    'style': num => 'STYLE' + num,
    // 'p': num => 'P' + num,
  }

  let htmlAbbreviations = {
    'src': [],
    'href': [],
    'svg': [],
    'class': [],
    'id': [],
    'script': [],
    'meta': [],
    'style': [],
    // 'p': [],
  };

  let compressedHTML = html;

  for (const index in regex) {
    let count = 0;
    let currRegex = regex[index];
    compressedHTML = compressedHTML.replace(currRegex, (match) => {
      htmlAbbreviations[index].push(match);
      return replacementTagAssigners[index](count++);
    });
  }

  try {
    const result = await openAI.createChatCompletion({
      model: "gpt-3.5-turbo-16k",
      messages: [
        {
          role: "user",
          content: "Make this website simple and clean, without losing content that is important for " +
            "finding a form to file for address change. Return back the HTML with all the abbreviations " +
            "same as in the provided HTML. In other words, it is vitally important that, for example, SRC1 in the " +
            "original, if conserved at all in your response, stays as SRC1 and not just SRC or SRC23. And same with, say URL2 or HREF3, or any " +
            "other things that are abbreviated HTML tags. That is because I am giving you a compressed file, and each of those" +
            " signifies a chunk of original file, shortened to fit your token limit. You are also not supposed to make up any new data " +
            "not found in this resource or in any other way introduce new information: you are only to refactor and throw away everything that isn't needed" +
            "to make what is important clear and simple to interact with. Your result needs to be a valid HTML, aside from the abbreviations:\n" + compressedHTML }]
    });


    console.log(result.data.choices, "\u001b[31mHERE ENDS THE INITIAL OUTPUT\u001b[0m");
    let decompressedHTML = result.data.choices[0].message.content;

    for (const currAbbrev in htmlAbbreviations) {
      let currAbbrevArray = htmlAbbreviations[currAbbrev];
      for (let i = currAbbrevArray.length - 1; i >= 0; --i) {
        decompressedHTML = decompressedHTML.replaceAll((currAbbrev + i).toUpperCase(), currAbbrevArray[i]);
      }
    }

    console.log(decompressedHTML);
  } catch (e) {
    console.log(e.response.data.error);
  }

  console.log("You got the gist, but type something again. Oh yeah, I want you to press those juicy buttons more");
});

