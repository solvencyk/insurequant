import sys
sys.path.insert(0, ".")
import e19_verify_plans as V
rel = "data/dart/FY2025_Q3/raw/KR0032_NH농협손해보험/20251114001790.xml"
print(V.cell_ctx(rel, 6059))
print(V.row_of(rel, 6059))
print(repr(V.lines_of(rel)[6058][:120]))
