import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from evals.calibration.harness import run_calibration
from evals.certificate import band_for, generate_certificate

WORKFLOW_NAME = "Refund Agent"
SCOPE = "Mock Refund Workflow"

st.title("Agent Reliability Audit Lab")

if "kappa" not in st.session_state:
    st.session_state.kappa = None

if st.button("Run Calibration"):
    st.session_state.kappa = run_calibration()

if st.session_state.kappa is None:
    st.info("Run calibration to produce a Cohen's Kappa score.")
else:
    st.metric("Cohen's Kappa", st.session_state.kappa)

if st.button("Generate Certificate"):
    kappa = st.session_state.kappa
    if kappa is None:
        st.warning("Run calibration before generating a certificate.")
    else:
        certificate = generate_certificate(
            WORKFLOW_NAME,
            SCOPE,
            kappa,
            band_for(kappa),
            a1_outcome=True,
        )
        st.markdown(certificate)