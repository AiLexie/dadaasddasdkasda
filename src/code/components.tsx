///<reference path="./types/ResizeObserver.d.ts"/>
import React from "/assets/react-fetcher.js";
import {bound} from "/assets/tools.js";

interface PopUpProperties {
  position?: "center" | "top-left";
}

export class PopUp extends React.Component<PopUpProperties> {
  public render() {
    return <div className={`popup popup-${this.props.position || "center"}`}>
      {this.props.children}
    </div>;
  }
}

interface PromptProperties {
  width: string;
}

export class Prompt extends React.Component<PromptProperties> {
  public render() {
    return <div className="prompt" style={{"width": this.props.width}}>
      {this.props.children}
    </div>;
  }
}

interface LoginPrompState {
  form: "login" | "signup";
}

export class LoginPrompt extends React.Component<{}, LoginPrompState> {
  public constructor(props: {}) {
    super(props);

    this.state = {
      "form": "login"
    };
  }

  @bound
  public switchForm() {
    this.setState({
      "form": this.state.form == "login" ? "signup" : "login"
    });
  }

  public render() {
    console.log(this.state.form == "login" ? true : false);
    return <PopUp>
      <Prompt width="300px">
        <h1>{this.state.form == "login" ? "Log In" : "Sign Up"}</h1>
        <br/>
        {this.state.form == "login" ? null : <InputBox id="invite" icon="📨" placeholder="Invite"/>}
        <InputBox id="username" icon="🙍‍♂️" placeholder="Username"/>
        <InputBox id="password" icon="🔑" placeholder="Password" password/>
        <br/>
        <a onClick={this.switchForm} role="button">{this.state.form == "login" ? "Don't have an account?" : "Already have an account?"}</a>
        <br/>
        <input type="button" value={this.state.form == "login" ? "Log In" : "Sign Up"}/>
      </Prompt>
    </PopUp>;
  }
}

interface InputBoxProperties {
  id: string;
  icon: string;
  placeholder: string;
  password?: boolean;
  hidden?: boolean;
}

interface InputBoxState {
  hidden: boolean;
}

export class InputBox extends React.Component<InputBoxProperties, InputBoxState> {
  private labelRef: React.RefObject<HTMLLabelElement>;

  constructor(props: InputBoxProperties) {
    super(props);

    console.log(props.hidden);

    this.labelRef = React.createRef();
    this.state = {"hidden": props.hidden || false};
  }

  public setShown(shown: boolean) {
    this.setState({"hidden": !shown});
  }

  public render() {
    const style = {...this.state.hidden ? {"display": "none"} : null};
    const type = this.props.password ? "password" : "text";
    return <div style={style} className="text-box">
      <label ref={this.labelRef} htmlFor={this.props.id}>
        <div>{this.props.icon}</div>
      </label>
      <input id={this.props.id} type={type} placeholder={this.props.placeholder} required/>
    </div>;
  }
}
