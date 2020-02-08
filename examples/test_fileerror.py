from PIL import Image
import sys
import traceback

def test(name):
  with open(name, 'rb') as f:
    try:
      image = Image.open(f)
      image.tobytes()
      print(name + ": Works")
    except Image.UnidentifiedImageError as e:
      print(name + ": Not an image")
    except OSError:
        print(name + ": Corrupt")
     # print(e)
    #  ex_type, ex_value, ex_traceback = sys.exc_info()
    #  trace_back = traceback.extract_tb(ex_traceback)
    #  stack_trace = list()
     # for trace in trace_back:
    #      stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))
     # print("Exception type : %s " % ex_type.__name__)
      #print("Exception message : %s" %ex_value)
      #print("Stack trace : %s" %stack_trace)
    except Exception as e2:
      print(name + ": Corrupt")
      #print(e2)

if __name__ == '__main__':
    test("./Video_of_Heat_shrink_tube_before_and_after.ogv")
    test("./Test.jpg")
    test("./BSicon_.svg")
    test("./River_GK_rojo_.png")
    test("./TSB_total_edits_(lifetime)_Dec_19_2018.png")
    test("./Handschoenen_(paar)_en_beschrijving_op_papier._objectnr_KA_15684.13.tif")
