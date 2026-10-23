(()=>{if(window.top!==window)return;const m=window.__pordaPromptStamp||"0";if(window.__pordaReloadPrompt===m)return;window.__pordaReloadPrompt=m;const y="porda-reload-prompt-dismissed:"+m,v=6e4,n=window.__pordaPromptText||{},a=(e,o)=>typeof e=="string"&&e.trim()?e:o,r={title:a(n.title,"PordaAI isn\u2019t running on this page"),body:a(n.body,"This tab was open before PordaAI installed, so images here aren\u2019t being checked. Reload to turn on protection."),reload:a(n.reload,"Reload now"),dismiss:a(n.dismiss,"Skip for now"),lang:a(n.lang,"en"),rtl:n.dir==="rtl"},s=e=>String(e).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");let t=null,i=null,d=null,l=null,x=!1;const u=()=>{try{return!!sessionStorage.getItem(y)}catch{return!1}};if(u())return;const T=e=>{if(!document.body)return;t=document.createElement("div"),t.dataset.pordaReloadPrompt="1",t.style.cssText=(e?["position:fixed","inset:0"]:["position:fixed",r.rtl?"left:16px":"right:16px","bottom:16px","width:auto"]).concat(["z-index:2147483647","pointer-events:auto"]).join(";");const o=t.attachShadow({mode:"closed"}),I=`
      <style>
        :host { all: initial; }
        /* The scrim is fixed in its own right, so it fills the viewport
           regardless of what all:initial does to the host's display.
           It also does real work beyond emphasis: it puts interim cover over
           an unprotected page while the user decides. */
        .scrim {
          position: fixed; inset: 0;
          display: flex; align-items: center; justify-content: center;
          background: rgba(0, 0, 0, 0.55);
        }
        .scrim .card { width: 380px; animation: pop 180ms ease-out; }
        @keyframes pop {
          from { opacity: 0; transform: scale(0.96); }
          to   { opacity: 1; transform: scale(1); }
        }
        .card {
          box-sizing: border-box;
          width: 320px;
          max-width: calc(100vw - 32px);
          padding: 16px;
          border-radius: 12px;
          background: #ffffff;
          border: 1px solid #e8e6e1;
          box-shadow: 0 10px 32px -8px rgba(15, 23, 42, 0.28);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                       Helvetica, Arial, sans-serif;
          color: #1a1a1a;
          animation: rise 220ms ease-out;
        }
        @keyframes rise {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .dot {
          /* Amber, not green: this card exists to say the page is NOT
             protected. A green dot signals the opposite of the message. */
          width: 8px; height: 8px; border-radius: 50%;
          background: #f59e0b; flex: 0 0 auto;
        }
        .title {
          margin: 0; font-size: 14px; font-weight: 600; color: #0a0a0a;
          line-height: 1.3;
        }
        .body {
          margin: 0 0 14px; font-size: 13px; line-height: 1.5; color: #5b5b5b;
        }
        .actions { display: flex; gap: 8px; }
        button {
          font: inherit; font-size: 13px; font-weight: 500;
          padding: 8px 14px; border-radius: 8px; cursor: pointer;
          border: 1px solid transparent; transition: background 140ms,
                                                     border-color 140ms;
        }
        /* all:initial on the host wipes the UA focus ring, so state it. */
        button:focus-visible { outline: 2px solid #0a0a0a; outline-offset: 2px; }
        .primary { background: #10b981; border-color: #10b981; color: #fff; flex: 1; }
        .primary:hover { background: #059669; border-color: #059669; }
        /* Quiet text button. The label is honest about the consequence, so the
           styling shouldn't also shove \u2014 strong primary, calm alternative. */
        .secondary { background: transparent; border-color: transparent; color: #8a8a8a; }
        .secondary:hover { background: #f6f5f1; color: #5b5b5b; }
        @media (prefers-color-scheme: dark) {
          .card { background: #1c1c1e; border-color: #333; color: #f2f2f2; }
          .title { color: #fff; }
          .body { color: #a8a8a8; }
          button:focus-visible { outline-color: #f2f2f2; }
          .secondary { color: #9a9a9a; }
          .secondary:hover { background: #2a2a2c; color: #c8c8c8; }
        }
      </style>
    `,E=`
      <div class="card" role="dialog" aria-modal="${e?"true":"false"}"
           aria-labelledby="porda-title" aria-live="polite"
           lang="${s(r.lang)}" dir="${r.rtl?"rtl":"ltr"}">
        <div class="head">
          <span class="dot"></span>
          <p class="title" id="porda-title">${s(r.title)}</p>
        </div>
        <p class="body">${s(r.body)}</p>
        <div class="actions">
          <button class="primary" id="porda-reload">${s(r.reload)}</button>
          <button class="secondary" id="porda-dismiss">${s(r.dismiss)}</button>
        </div>
      </div>
    `;o.innerHTML=I+(e?`<div class="scrim">${E}</div>`:E),o.getElementById("porda-reload").addEventListener("click",()=>{f(),location.reload()}),o.getElementById("porda-dismiss").addEventListener("click",()=>{try{sessionStorage.setItem(y,"1")}catch{}f()}),document.documentElement.appendChild(t);const p=document.activeElement;!!p&&(p.tagName==="INPUT"||p.tagName==="TEXTAREA"||p.isContentEditable)||o.getElementById("porda-reload").focus(),e&&(l=c=>{if(c.key==="Escape"){c.preventDefault(),b();return}if(c.key!=="Tab")return;const h=o.getElementById("porda-reload"),k=o.getElementById("porda-dismiss");!h||!k||(c.preventDefault(),(o.activeElement===h?k:h).focus())},document.addEventListener("keydown",l,!0)),S()},f=()=>{if(clearTimeout(i),i=null,d&&(document.removeEventListener("visibilitychange",d),d=null),l&&(document.removeEventListener("keydown",l,!0),l=null),t){try{t.remove()}catch{}t=null}},S=()=>{clearTimeout(i),i=setTimeout(b,v),d=()=>{document.visibilityState==="visible"?(clearTimeout(i),i=setTimeout(b,v)):(clearTimeout(i),i=null)},document.addEventListener("visibilitychange",d)},b=()=>{f(),w()},w=()=>{if(u())return;const e=()=>{document.visibilityState==="visible"&&(document.removeEventListener("visibilitychange",e),g())};document.addEventListener("visibilitychange",e)},g=()=>{if(!(u()||t)){if(!document.body){document.addEventListener("DOMContentLoaded",g,{once:!0});return}T(!x),x=!0}};document.visibilityState==="visible"?g():w()})();
