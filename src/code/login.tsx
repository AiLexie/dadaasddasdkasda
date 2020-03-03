import React from "/assets/react-fetcher.js";
import ReactDOM from "/assets/react-dom-fetcher.js";
import * as Components from "/assets/components.js";

const content = <Components.LoginPrompt/>
ReactDOM.render(content, document.getElementById("mount"));
