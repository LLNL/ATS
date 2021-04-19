"""
  CLASSES: nightly

  Test Case:  example_script.py

"""

OpenDatabase(data_path("noise.silo"))


#
# Test simple read and display of a variable
#
AddPlot("Pseudocolor","hardyglobal")
DrawPlots()

Test("example_render_test_00")

#
# Change the view and re-render
#

v=GetView3D()
v.viewNormal=(-0.5, 0.296198, 0.813798)
SetView3D(v)
Test("example_render_test_01")

#
# Run a query to get the volume of the entire dataset
#


Query("Volume")
v = GetQueryOutputValue()
TestText("example_text_test_00",
         "Volume = %0.2f" % v)


#
# Add an isovolume operator to select a submesh.
#

AddOperator("Isovolume")
iatts = IsovolumeAttributes()
iatts.lbound = 4
iatts.ubound = 1e+37
iatts.variable = "default"
SetOperatorOptions(iatts)
DrawPlots()


#
# re-render after isovolume
#
Test("example_render_test_02")

#
# Check new volume
#
Query("Volume",use_actual=True)
v = GetQueryOutputValue()
TestText("example_text_test_01",
         "Volume = %0.2f" % v)


Exit()
