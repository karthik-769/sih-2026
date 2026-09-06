"""
OIL (Oil India Limited) Realistic Safety Report Dataset Generator.
Generates realistic upstream/midstream oilfield safety observations with ~16% SIF precursor density.
Can export to CSV or directly seed the local database.
"""

import os
import sys
import csv
import random
import argparse
from datetime import datetime, timedelta, timezone

# Ensure backend path is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

OIL_LOCATIONS = [
    {"name": "Duliajan Central Complex", "site": "Duliajan", "field": "Assam Fields", "installation": "Central Processing Facility"},
    {"name": "Digboi Refinery Block 4", "site": "Digboi", "field": "Digboi Basin", "installation": "Crude Distillation Unit 4"},
    {"name": "Moran Wellpad #14", "site": "Moran", "field": "Moran Field", "installation": "Workover Rig #14"},
    {"name": "Jorhat Pumping Station", "site": "Jorhat", "field": "Upper Assam Grid", "installation": "Crude Oil Pumping Station #2"},
    {"name": "Naharkatia GGS-3", "site": "Naharkatia", "field": "Naharkatia Field", "installation": "Gas Gathering Station 3"},
    {"name": "Baghjan EPS-2", "site": "Baghjan", "field": "Baghjan Field", "installation": "Early Production Facility #2"},
    {"name": "Kumchai Rig #7", "site": "Kumchai", "field": "Arunachal Foothills", "installation": "Deep Drilling Rig #7"},
]

OIL_DEPARTMENTS = [
    {"name": "Drilling & Workover", "desc": "Drilling rigs, workover operations, well control, casing & cementing"},
    {"name": "Production & Processing", "desc": "Oil & gas separation, dehydrators, gas compression, flowlines"},
    {"name": "Pipeline Operations", "desc": "Crude & natural gas transmission pipelines, pigging, cathodic protection"},
    {"name": "Mechanical Maintenance", "desc": "Rotating equipment, pumps, compressors, valves, diesel generators"},
    {"name": "Electrical & Instrumentation", "desc": "High-voltage substations, switchgear, DCS, PLC control systems"},
    {"name": "HSE & Field Safety", "desc": "Atmospheric gas monitoring, emergency response, permit-to-work compliance"},
]

JOB_ROLES = [
    "Drilling Rig Supervisor", "Roughneck / Floorhand", "Derrickman", "Mud Logger",
    "Production Operator", "Mechanical Maintenance Technician", "High Voltage Electrician",
    "Instrumentation & Control Engineer", "Pipeline Inspector", "Scaffolding Rigger",
    "Welder / Fabricator", "Crane Operator / Rigger", "Process Chemist", "HSE Officer"
]

SIF_SCENARIOS = [
    {
        "activity": "Confined Space Entry",
        "category": "Confined Space",
        "rule": "Confined Space",
        "barrier": "Atmospheric Testing",
        "actual": "No injury (Near-miss)",
        "potential": "Fatal Asphyxiation / Toxic Gas Inhalation (H2S)",
        "fatality": True,
        "templates": [
            "Worker entered crude oil storage vessel V-102 for sludge desanding without conducting gas testing for H2S and hydrocarbons. No standby sentry stationed at vessel manway.",
            "Technician entered underground separator drainage pit to isolate stuck drain valve without atmospheric testing or confined space entry permit. Oxygen level was unverified.",
            "Two contractors descended into mud tank pit #3 without continuous toxic gas monitoring. Standby watchman was absent from the entrance."
        ]
    },
    {
        "activity": "Pump Maintenance",
        "category": "Energy Isolation",
        "rule": "Energy Isolation",
        "barrier": "LOTO / Energy Isolation",
        "actual": "No injury",
        "potential": "Fatal Electrocution / Arc-Flash Blast (6.6kV)",
        "fatality": True,
        "templates": [
            "During 6.6kV mainline crude transfer pump motor overhaul, technician opened motor terminal box without applying LOTO padlock and tagout on breaker 4A. Circuit was live.",
            "Mechanic started replacing impeller mechanical seal on high-pressure water injection pump while suction manifold remained pressurized at 120 bar without double block and bleed isolation.",
            "Electrician began troubleshooting gas compressor feeder panel without verifying zero energy state with calibrated multimeter. Breaker was not locked out."
        ]
    },
    {
        "activity": "Rig Mast Maintenance",
        "category": "Working at Height",
        "rule": "Work at Height",
        "barrier": "Fall Protection",
        "actual": "No injury (Near-miss)",
        "potential": "Fatal Fall from 18m Rig Mast Elevation",
        "fatality": True,
        "templates": [
            "Derrickman climbed to monkey board at 24m elevation on Kumchai Rig #7 with retractable fall arrest inertia reel disconnected from safety harness dorsal D-ring.",
            "Contractor rigger walked along unprotected edge of temporary scaffold at 11m elevation above flare knockout drum without 100% tie-off connection.",
            "Maintenance technician removed floor grating on upper platform of Moran Wellpad #14 workover rig without installing perimeter warning barricade or safety harness tether."
        ]
    },
    {
        "activity": "Heavy Rigging & Lifting",
        "category": "Lifting & Rigging",
        "rule": "Line of Fire",
        "barrier": "Barricades / Exclusion Zone",
        "actual": "No injury (Near-miss)",
        "potential": "Fatal Crush Injury from Dropped 8-Ton Blowout Preventer (BOP)",
        "fatality": True,
        "templates": [
            "While crane was hoisting 8-ton BOP stack over wellhead cellar, two roustabouts walked directly underneath the suspended load to guide alignment without tag lines.",
            "Crane operator lifted 5-ton mud pump skid across active pedestrian walkway. Exclusion drop-zone barrier tape was omitted and workers were in line of fire.",
            "Webbing sling showed 30% fiber cut across edge but was used to lift 3.5-ton casing spool. Lift was halted after sling slipped 15 cm on lifting shackle."
        ]
    },
    {
        "activity": "Hot Work on Hydrocarbon Line",
        "category": "Hot Work",
        "rule": "Hot Work",
        "barrier": "Hot Work Permit / Spark Containment",
        "actual": "No injury",
        "potential": "Catastrophic Hydrocarbon Explosion & Multi-Fatality Deflagration",
        "fatality": True,
        "templates": [
            "Welder began grinding on gas gathering manifold branch line within 5 meters of active flange leak without hot work permit, gas check, or fire blanket containment.",
            "Oxy-acetylene cutting torch ignited adjacent oily rags in crude storage manifold bund due to missing spark arrestor enclosure and lack of designated fire watch.",
            "Contractor performed welding on structural skid adjacent to Baghjan condensate tank while flare line was venting gas without pre-weld explosimeter test."
        ]
    },
]

NON_SIF_SCENARIOS = [
    {
        "activity": "Routine Housekeeping",
        "category": "General Operations",
        "rule": "Line of Fire",
        "barrier": "Housekeeping / Walkways",
        "actual": "No injury",
        "potential": "Minor Slip / Bruise",
        "fatality": False,
        "templates": [
            "Small puddle of lube oil observed near diesel generator DG-2 base frame. Absorbent pad applied and spill cleaned up promptly.",
            "Uncoiled 1-inch washdown water hose left across warehouse walkway creating a minor trip hazard. Hose rolled back onto storage drum.",
            "Empty wooden shipping crate left in front of emergency eye-wash station. Moved immediately to designated scrap yard."
        ]
    },
    {
        "activity": "PPE Compliance Observation",
        "category": "Safe Practice",
        "rule": "Working with Hazardous Substances",
        "barrier": "PPE",
        "actual": "No injury",
        "potential": "Minor Eye Irritation",
        "fatality": False,
        "templates": [
            "Visitor observed walking near chemical injection skid without wearing safety glasses. Correct PPE provided prior to entering active zone.",
            "Contractor driver entered crude loading terminal wearing open-toe footwear. Turned back at gate until steel-toe safety boots were worn.",
            "Positive observation: Maintenance crew wore full chemical splash suits, nitrile gloves, and face shields while handling corrosion inhibitor biocides."
        ]
    },
    {
        "activity": "Safe Controlled Work",
        "category": "Safe Practice",
        "rule": "Confined Space",
        "barrier": "Safe Operational Practice",
        "actual": "No injury",
        "potential": "None (Fully Controlled)",
        "fatality": False,
        "templates": [
            "Vessel V-201 cleaning executed strictly under Confined Space Permit. Gas testing verified 20.9% O2, 0 ppm H2S, and standby watchman was continuously stationed.",
            "Pump P-101 motor replacement completed under verified LOTO with lock box and zero-energy test verified by lead electrical engineer.",
            "Scaffolding inspection completed at 15m elevation on Digboi CDU-4 column. Green Scafftag applied and full 100% tie-off harness used throughout."
        ]
    },
    {
        "activity": "Equipment Integrity Check",
        "category": "Maintenance & Integrity",
        "rule": "Pressure Systems",
        "barrier": "Preventative Maintenance",
        "actual": "Minor seep",
        "potential": "Equipment Minor Leak",
        "fatality": False,
        "templates": [
            "Routine shift walkaround identified minor weeping gland packing on 2-inch gate valve GV-304. Packing nut tightened to specification.",
            "Pressure gauge PG-12 on nitrogen bottle manifold was out of calibration by 0.5 bar. Gauge tagged out and replaced with calibrated unit.",
            "Corrosion spotted on external paint coating of natural gas flowline spool. Scheduled for ultrasonic wall thickness check and repainting."
        ]
    }
]


def generate_oil_dataset(count: int = 5000, target_sif_density: float = 0.16) -> list:
    """
    Generates realistic OIL safety reports with specified count and SIF precursor density (~16%).
    """
    reports = []
    now = datetime.now(timezone.utc)
    num_sif = int(count * target_sif_density)
    num_non_sif = count - num_sif

    all_scenarios = [("SIF", s) for s in SIF_SCENARIOS] * (num_sif // len(SIF_SCENARIOS) + 1)
    all_scenarios = all_scenarios[:num_sif]

    non_sif_scenarios = [("NON_SIF", s) for s in NON_SIF_SCENARIOS] * (num_non_sif // len(NON_SIF_SCENARIOS) + 1)
    non_sif_scenarios = non_sif_scenarios[:num_non_sif]

    combined = all_scenarios + non_sif_scenarios
    random.seed(42)  # Deterministic seed for reproducible evaluation datasets
    random.shuffle(combined)

    for idx, (kind, sc) in enumerate(combined, start=1):
        loc = random.choice(OIL_LOCATIONS)
        dept = random.choice(OIL_DEPARTMENTS)
        role = random.choice(JOB_ROLES)
        desc_template = random.choice(sc["templates"])
        
        # Add slight naturalistic variation
        case_id = f"OIL-{now.year}-{idx:05d}"
        days_ago = random.uniform(0, 90)
        reported_time = now - timedelta(days=days_ago)

        if kind == "SIF":
            incident_type = random.choice(["UNSAFE_ACT", "UNSAFE_CONDITION", "NEAR_MISS"])
        else:
            if "Safe Controlled" in sc["activity"]:
                incident_type = "SAFETY_OBSERVATION"
            else:
                incident_type = random.choice(["UNSAFE_ACT", "UNSAFE_CONDITION", "SAFETY_OBSERVATION"])

        reports.append({
            "case_id": case_id,
            "job_role": role,
            "department_name": dept["name"],
            "location_name": loc["name"],
            "site": loc["site"],
            "field": loc["field"],
            "installation": loc["installation"],
            "task": sc["activity"],
            "activity": sc["activity"],
            "activity_category": sc["category"],
            "incident_type": incident_type,
            "description": desc_template,
            "actual_consequence": sc["actual"],
            "potential_consequence": sc["potential"],
            "fatality_potential": sc["fatality"],
            "life_saving_rule": sc["rule"],
            "failed_barrier": sc["barrier"],
            "is_sif": (kind == "SIF"),
            "reported_at": reported_time.isoformat(),
        })

    return reports


def export_to_csv(reports: list, filepath: str):
    """Exports generated reports to CSV."""
    if not reports:
        return
    keys = list(reports[0].keys())
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(reports)
    print(f"Exported {len(reports)} OIL reports to {filepath}")


def seed_oil_database(count: int = 500):
    """Directly populates the running database with OIL data and runs AI analysis."""
    from app.database.session import SessionLocal
    from app.models import Department, Location, SafetyReport, IncidentType, ProcessingStatus, User, UserRole
    from app.services.analysis import analysis_service

    db = SessionLocal()
    try:
        print(f"Seeding database with {count} realistic OIL safety reports...")
        
        # Ensure OIL Departments exist
        dept_map = {}
        for d in OIL_DEPARTMENTS:
            obj = db.query(Department).filter(Department.name == d["name"]).first()
            if not obj:
                obj = Department(name=d["name"], description=d["desc"])
                db.add(obj)
                db.flush()
            dept_map[d["name"]] = obj.id

        # Ensure OIL Locations exist
        loc_map = {}
        for l in OIL_LOCATIONS:
            obj = db.query(Location).filter(Location.name == l["name"]).first()
            if not obj:
                obj = Location(name=l["name"], description=f"{l['installation']}, {l['site']}")
                db.add(obj)
                db.flush()
            loc_map[l["name"]] = obj.id

        # Get default user for submission
        user = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not user:
            user = db.query(User).first()
        user_id = user.id if user else None

        reports_data = generate_oil_dataset(count=count, target_sif_density=0.16)
        created_count = 0

        for r in reports_data:
            existing = db.query(SafetyReport).filter(SafetyReport.case_id == r["case_id"]).first()
            if existing:
                continue

            dt = datetime.fromisoformat(r["reported_at"])
            report = SafetyReport(
                case_id=r["case_id"],
                job_role=r["job_role"],
                department_id=dept_map[r["department_name"]],
                location_id=loc_map[r["location_name"]],
                site=r["site"],
                field=r["field"],
                installation=r["installation"],
                task=r["task"],
                activity=r["activity"],
                activity_category=r["activity_category"],
                incident_type=IncidentType[r["incident_type"]],
                description=r["description"],
                actual_consequence=r["actual_consequence"],
                potential_consequence=r["potential_consequence"],
                fatality_potential=r["fatality_potential"],
                life_saving_rule=r["life_saving_rule"],
                reported_at=dt,
                created_by=user_id,
                processing_status=ProcessingStatus.SUBMITTED,
            )
            db.add(report)
            db.flush()

            # Trigger AI Analysis pipeline
            analysis_service.process_report_analysis(report_id=report.id, db=db)
            created_count += 1
            if created_count % 25 == 0:
                print(f"Processed {created_count}/{len(reports_data)} reports through AI Pipeline...")
                db.commit()

        db.commit()
        print(f"Successfully created and AI-analyzed {created_count} OIL reports in database!")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic OIL SIF Dataset")
    parser.add_argument("--count", type=int, default=5000, help="Number of records to generate")
    parser.add_argument("--csv", type=str, default="oil_safety_dataset_5000.csv", help="CSV output path")
    parser.add_argument("--seed-db", action="store_true", help="Populate the local database with records")
    parser.add_argument("--seed-count", type=int, default=150, help="Number of records to seed in local DB")

    args = parser.parse_args()

    data = generate_oil_dataset(count=args.count, target_sif_density=0.16)
    csv_path = os.path.join(BASE_DIR, "samples", args.csv)
    export_to_csv(data, csv_path)

    if args.seed_db:
        seed_oil_database(count=args.seed_count)
