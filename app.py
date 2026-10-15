import streamlit as st
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

st.set_page_config(
    page_title="EcoSort | Smart Waste Segregation",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f4f8f3; color: #17251d; }
.block-container { padding-top: 1.35rem; max-width: 1250px; }
.hero { background: linear-gradient(120deg,#123c2c 0%,#176044 65%,#23794f 100%); padding:30px 34px; border-radius:24px; color:white; margin-bottom:22px; box-shadow:0 12px 30px rgba(18,60,44,.12); }
.hero h1 { font-family:'Manrope',sans-serif; color:white; font-size:2.35rem; margin:8px 0; }
.hero p { color:#e0f1e5; font-size:1rem; max-width:760px; margin-bottom:0; }
.eyebrow { letter-spacing:2px; font-size:.72rem; font-weight:800; color:#b7edc8; }
.metric-card,.result-card,.info-card { background:white; border:1px solid #e1eae1; border-radius:18px; padding:19px; box-shadow:0 5px 18px rgba(23,37,29,.035); }
.small-label { font-size:.75rem; color:#718078; font-weight:700; text-transform:uppercase; letter-spacing:.8px; }
.big-number { font-family:'Manrope',sans-serif; font-size:1.45rem; font-weight:800; color:#174c34; margin-top:5px; }
.section-title { font-family:'Manrope',sans-serif; font-weight:800; font-size:1.22rem; margin:8px 0 4px; }
.muted { color:#6b7b70; font-size:.92rem; }
.pill { display:inline-block; background:#e7f5e9; color:#17613c; padding:5px 10px; border-radius:999px; font-size:.78rem; font-weight:700; }
.bin-card { background:white; border:1px solid #e1eae1; border-radius:18px; padding:20px; margin:12px 0; }
.bin-icon { width:82px; min-width:82px; height:100px; border-radius:14px; display:flex; flex-direction:column; justify-content:center; align-items:center; color:white; box-shadow:inset 0 -8px 0 rgba(0,0,0,.08); }
.step-row { background:white; border:1px solid #e6ede5; padding:12px 14px; border-radius:12px; margin-bottom:8px; }
div[data-testid="stFileUploader"] { background:white; border:1.5px dashed #a8c8b1; border-radius:16px; padding:14px; }
.stButton > button { border-radius:12px; min-height:3rem; font-weight:700; }
.stButton > button[kind="primary"] { background:#17613c; border:0; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# Bin colour is a suggested routing label, not a universal rule.
# Special waste must follow local municipal and authorised collection guidance.
CATEGORIES = {
    "Plastic": {
        "prompt": "a photo of ordinary recyclable plastic waste such as a plastic bottle, food container or plastic packaging",
        "bin": "Blue",
        "bin_name": "Dry recyclable waste (verify local rules)",
        "bin_color": "#2478D4",
        "icon": "🧴",
        "action": "Clean, empty recyclable plastic is generally handled through the dry-waste stream.",
        "steps": [
            "Empty leftover liquid or food.",
            "Rinse if needed and allow it to drain.",
            "Keep it separate from wet food waste.",
            "Place it in the locally designated dry-waste collection stream."
        ],
        "caution": "Flexible wrappers and multilayer packaging may not be accepted by every recycler."
    },
    "Paper": {
        "prompt": "a photo of recyclable paper or cardboard waste such as newspaper, office paper or a cardboard box",
        "bin": "Blue",
        "bin_name": "Dry recyclable waste (verify local rules)",
        "bin_color": "#2478D4",
        "icon": "📄",
        "action": "Clean, dry paper and cardboard can usually be collected with recyclable dry waste.",
        "steps": [
            "Remove non-paper parts when practical.",
            "Flatten cardboard boxes.",
            "Keep the paper clean and dry.",
            "Place it in the locally designated dry-waste stream."
        ],
        "caution": "Paper soaked with oil or food may not be recyclable through ordinary paper collection."
    },
    "Metal": {
        "prompt": "a photo of an ordinary recyclable metal item such as an aluminium drink can or tin can",
        "bin": "Blue",
        "bin_name": "Dry recyclable waste (verify local rules)",
        "bin_color": "#2478D4",
        "icon": "🥫",
        "action": "Empty metal cans and containers are generally suitable for dry recyclable-waste collection.",
        "steps": [
            "Empty the container.",
            "Rinse if needed and allow it to drain.",
            "Avoid sharp edges and do not handle damaged metal carelessly.",
            "Use the locally designated dry-waste collection stream."
        ],
        "caution": "Batteries, chemical containers, pressurised cans and sharp metal may require special handling."
    },
    "Glass": {
        "prompt": "a photo of an ordinary glass bottle, glass jar or glass container waste",
        "bin": "Blue",
        "bin_name": "Dry waste — confirm glass collection locally",
        "bin_color": "#2478D4",
        "icon": "🍾",
        "action": "Glass may be collected separately or through an approved dry-waste route, depending on local arrangements.",
        "steps": [
            "Empty the bottle or jar.",
            "Keep intact glass protected from breakage.",
            "Check whether your collector accepts glass in dry waste.",
            "Do not handle broken glass with bare hands; secure it and follow local safety instructions."
        ],
        "caution": "Never leave loose broken glass where it could injure household members or sanitation workers."
    },
    "Organic": {
        "prompt": "a photo of biodegradable food or garden waste such as fruit peels, vegetable scraps, leaves or leftover food",
        "bin": "Green",
        "bin_name": "Wet / biodegradable waste (verify local rules)",
        "bin_color": "#278447",
        "icon": "🍌",
        "action": "Suitable food scraps and biodegradable garden waste generally belong in wet-waste collection or appropriate composting.",
        "steps": [
            "Separate scraps from plastic wrappers and other packaging.",
            "Put suitable scraps into the designated wet-waste container.",
            "Keep dry recyclables out of wet waste.",
            "Follow your local collection or composting instructions."
        ],
        "caution": "Not every product labelled biodegradable is accepted by every composting system."
    },
    "E-waste": {
        "prompt": "a photo of electronic waste such as an old mobile phone, computer keyboard, charger, circuit board, mouse or electronic cable",
        "bin": "Special collection",
        "bin_name": "Authorised e-waste collection — not ordinary household bins",
        "bin_color": "#6D4CC3",
        "icon": "🔌",
        "action": "Electronic devices and components should be kept separate and handed to an authorised e-waste collection centre, producer take-back programme or approved recycler.",
        "steps": [
            "Keep the device separate from wet and dry household waste.",
            "If practical, back up and erase personal data before handing over a phone or computer.",
            "Do not dismantle electronics unless qualified to do so.",
            "Take it to an authorised e-waste collection point or use a producer take-back programme."
        ],
        "caution": "Do not put electronic devices or batteries in ordinary bins or fire. If a battery is swollen, hot, leaking or damaged, avoid handling it and seek specialist guidance."
    },
    "Sanitary waste": {
        "prompt": "a photo of sanitary or menstrual waste such as a used sanitary pad, menstrual hygiene product or discarded menstrual cloth",
        "bin": "Separate sanitary handling",
        "bin_name": "Wrapped sanitary waste / local collection instructions",
        "bin_color": "#B45379",
        "icon": "🩹",
        "action": "Used disposable menstrual products should be wrapped securely and placed in the sanitary-waste stream or other method specified by the local collection provider. A reusable menstrual cloth intended for reuse should be washed and completely dried, not thrown away after each use.",
        "steps": [
            "If it is a used disposable pad or similar product, do not flush it down the toilet.",
            "Wrap the used item securely in paper or its product wrapper, as appropriate.",
            "Use the designated sanitary-waste collection route provided locally.",
            "If discarding a reusable menstrual cloth, wrap it and follow local guidance for sanitary textiles; do not place it loose in recycling."
        ],
        "caution": "Sanitary-waste collection rules vary. Handle hygienically, wash hands afterward, and follow local municipal instructions. The image model may not reliably distinguish a menstrual cloth from ordinary fabric."
    },
    "Hazardous waste": {
        "prompt": "a photo of household hazardous waste such as a chemical bottle, pesticide container, paint can, cleaning chemical or aerosol can",
        "bin": "Hazardous waste collection",
        "bin_name": "Separate authorised collection — not ordinary bins",
        "bin_color": "#C24135",
        "icon": "⚠️",
        "action": "Potentially hazardous household chemicals need product-specific handling and an appropriate authorised collection route.",
        "steps": [
            "Do not mix chemicals or pour unknown contents into drains.",
            "Keep the material in its original labelled container if it is safe to do so.",
            "Keep it away from children, heat and ignition sources.",
            "Contact your local waste authority or an authorised hazardous-waste facility for disposal instructions."
        ],
        "caution": "The model cannot identify chemical contents or determine risk from an image alone. Do not open, smell, touch or move leaking or unknown containers."
    },
}

@st.cache_resource(show_spinner=False)
def load_model():
    model_id = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_id)
    processor = CLIPProcessor.from_pretrained(model_id)
    model.eval()
    return model, processor

def predict(image):
    model, processor = load_model()
    labels = list(CATEGORIES.keys())
    prompts = [CATEGORIES[label]["prompt"] for label in labels]
    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probabilities = torch.softmax(outputs.logits_per_image[0], dim=0)
    ranked = [
        {"category": labels[i], "score": float(probabilities[i])}
        for i in range(len(labels))
    ]
    return sorted(ranked, key=lambda item: item["score"], reverse=True)

# Sidebar
with st.sidebar:
    st.markdown("## ♻️ EcoSort")
    st.caption("Smart Waste Segregation")
    st.divider()
    st.markdown("### Workflow")
    st.markdown("1. Upload an image\n2. Identify likely category\n3. See suggested collection route\n4. Follow disposal and safety steps")
    st.divider()
    st.markdown("### Supported categories")
    for name, item in CATEGORIES.items():
        st.markdown(f"{item['icon']} **{name}**")
    st.divider()
    st.caption("Team Quantum Coders")
    st.caption("Sri Sairam College of Engineering")

# Header
st.markdown("""
<div class="hero">
  <div class="eyebrow">QUANTUM CODERS · SUSTAINABLE TECHNOLOGY</div>
  <h1>Waste less. Sort smarter.</h1>
  <p>Identify common waste from a photo and learn the suggested collection route and safe disposal steps — including e-waste and sanitary waste.</p>
</div>
""", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f'<div class="metric-card"><div class="small-label">Waste categories</div><div class="big-number">{len(CATEGORIES):02d}</div><div class="muted">Everyday and special waste</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><div class="small-label">Analysis method</div><div class="big-number">Vision AI</div><div class="muted">Pretrained CLIP image-language model</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="small-label">Guidance</div><div class="big-number">Step by step</div><div class="muted">Bin route · preparation · safety</div></div>', unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown('<div class="section-title">01 / Upload a waste image</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Use one clear item per photo. Special waste can be difficult to classify visually.</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop an image here or browse files", type=["jpg", "jpeg", "png", "webp"])
    image = None
    if uploaded:
        try:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Image ready for analysis", use_container_width=True)
        except Exception:
            st.error("Could not open that image. Please choose another file.")
    else:
        st.markdown("""
        <div class="info-card" style="text-align:center;padding:38px 18px;">
          <div style="font-size:3rem;">📷</div>
          <h3>Your image goes here</h3>
          <div class="muted">Try a bottle, food scraps, old phone, used sanitary product package or labelled chemical container.</div>
        </div>
        """, unsafe_allow_html=True)
    analyze_clicked = st.button("✦  Analyze waste item", type="primary", use_container_width=True, disabled=image is None)
    if st.button("↻  Clear result", use_container_width=True):
        st.session_state.pop("ranked", None)
        st.rerun()

with right:
    st.markdown('<div class="section-title">02 / Identification and disposal guide</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Category, collection route, preparation steps and safety advice.</div>', unsafe_allow_html=True)

    if analyze_clicked and image is not None:
        try:
            with st.spinner("Analyzing image… first use may download model files."):
                st.session_state["ranked"] = predict(image)
        except Exception as error:
            st.error("The model could not run. Check internet access and installed dependencies.")
            st.code(str(error))

    ranked = st.session_state.get("ranked")
    if ranked:
        top = ranked[0]
        category = top["category"]
        details = CATEGORIES[category]
        score = top["score"]

        if score < 0.25:
            st.warning("The model's relative score is low. Verify this result manually.")
        if category in ("E-waste", "Sanitary waste", "Hazardous waste"):
            st.warning("Special-waste predictions can be unreliable from images alone. Read the guidance carefully and verify the item.")

        st.markdown(f"""
        <div class="result-card">
          <div class="small-label">Likely category</div>
          <div style="display:flex;align-items:center;gap:12px;margin:12px 0;">
            <div style="font-size:2.7rem;">{details['icon']}</div>
            <div>
              <div style="font-family:Manrope,sans-serif;font-size:1.7rem;font-weight:800;color:#174c34;">{category}</div>
              <span class="pill">Review the disposal guidance below</span>
            </div>
          </div>
          <div class="small-label">Relative model score — not validated accuracy</div>
          <div style="font-size:1.4rem;font-weight:800;margin:5px 0 10px;">{score*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(max(score, 0.0), 1.0))

        st.markdown("### 🗑️ Where should it go?")
        st.markdown(f"""
        <div class="bin-card">
          <div style="display:flex;align-items:center;gap:17px;">
            <div class="bin-icon" style="background:{details['bin_color']};">
              <span style="font-size:30px;">{details['icon']}</span>
              <span style="font-size:11px;font-weight:800;text-align:center;padding:0 3px;">{details['bin'].upper()}</span>
            </div>
            <div>
              <div class="small-label">Suggested collection route</div>
              <div style="font-family:Manrope,sans-serif;font-size:1.35rem;font-weight:800;color:{details['bin_color']};">{details['bin']}</div>
              <div style="font-weight:700;color:#263a2d;">{details['bin_name']}</div>
            </div>
          </div>
          <p style="margin:17px 0 0;color:#45564b;">{details['action']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ✅ How to dispose of it")
        for i, step in enumerate(details["steps"], start=1):
            st.markdown(f"""
            <div class="step-row">
              <span style="display:inline-block;background:#e7f5e9;color:#17613c;border-radius:50%;width:27px;height:27px;text-align:center;line-height:27px;font-weight:800;margin-right:8px;">{i}</span>
              <span style="color:#263a2d;">{step}</span>
            </div>
            """, unsafe_allow_html=True)

        st.warning(f"Safety note: {details['caution']}")
        st.info("Bin colours and collection routes vary by municipality. Special waste must not automatically be placed in ordinary household bins. Follow local municipal guidance and authorised collection instructions.")

        with st.expander("See alternative model predictions"):
            for alternative in ranked[1:]:
                st.write(f"**{alternative['category']}** — relative model score {alternative['score']*100:.1f}%")
                st.progress(min(max(alternative["score"], 0.0), 1.0))

        st.caption("Prototype limitation: CLIP is a general pretrained image-language model, not a waste-specific model validated on a dedicated test set. It may confuse cloth with sanitary products or electronics with ordinary objects. Its score is not measured accuracy or a calibrated probability.")
    else:
        st.markdown("""
        <div class="info-card" style="padding:26px;">
          <div style="font-size:2rem;">🧭</div>
          <h3>Your disposal guide will appear here</h3>
          <p class="muted">Upload an image and select <b>Analyze waste item</b>. EcoSort will rank eight categories and show the suggested collection route and safety instructions.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("#### Image tips")
        st.markdown("- Use one clearly visible item\n- Use good lighting\n- Avoid cluttered backgrounds\n- For hazardous products, never open a container just to take a photo")

st.divider()
c1, c2 = st.columns([1.3, 1])
with c1:
    st.markdown("### 🌱 Why EcoSort?")
    st.write("EcoSort helps users understand the likely waste category and take a safer next step, including for items that need specialist collection.")
with c2:
    st.markdown("### 🌍 Impact alignment")
    st.markdown("**SDG 12** · Responsible Consumption and Production  \n**SDG 11** · Sustainable Cities and Communities  \n**SDG 13** · Climate Action")
st.caption("Team Quantum Coders · Sri Sairam College of Engineering · Prototype showcase build")
