'''
Utilities for Procedural IDE.
G{importgraph}
'''
import logging

import os
import random

import wx
import wx.combo
import wx.lib.platebtn as platebtn
import wx.lib.agw.floatspin as FS
import Image

log = logging.getLogger()

APP_PATH = os.path.abspath(os.getcwd())

YELLOW = '#FFF8AC'
LIGHT_YELLOW = '#FFF8DC'
MOD_COLOR = YELLOW

class PIDEException(Exception):
    pass

def app_abs_path(*rel_path):
    '''
    Make path absolute by prepending app path.
    '''
    o = os.path

    path = o.join(APP_PATH, o.dirname(__file__))
    path = o.normpath(path)

    rel_path = o.join(*rel_path) if rel_path else ''
    return o.join(path, rel_path)

def load_image(fname, size):
    image = Image.open(fname)
    if image.size != size:
        image = image.resize(size, 1)

    wimage = wx.EmptyImage(*size)
    wimage.SetData(image.convert('RGB').tostring())
    wimage.SetAlphaData(image.convert("RGBA").tostring()[3::4])
    return wimage.ConvertToBitmap()

class ContainerPanel(wx.Panel):
    def __init__(self, parent, _id, size=wx.DefaultSize,
                 pos=wx.DefaultPosition):
        wx.Panel.__init__(self, parent, _id, size=size, pos=pos)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

#----------------------------------------------------------------------
# This class is a popup containing a CheckListBox.

class CheckListComboPopup(wx.combo.ComboPopup):
    def __init__(self, _parent, choices, on_change=None):
        wx.combo.ComboPopup.__init__(self)

        self.choices = choices
        self._parent = _parent
        self.on_change = on_change

    # overridden ComboPopup methods

    def Init(self):
        self.value = []
        self.curitem = None
        self.lb = None

    def Create(self, parent):
        self.lb = wx.CheckListBox(parent, -1, choices=self.choices)
        self.lb.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def GetControl(self):
        return self.lb

    def GetStringValue(self):
        return ','.join(self.value)

    def SetValue(self, value):
        index = self.choices.index(value)
        self.value.append(value)
        self.lb.SetCheckedStrings(self.value)

    def OnPopup(self):
        if self.value:
            self.lb.EnsureVisible(self.choices.index(self.value[0]))

    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
#        return wx.DefaultSize #(minWidth, min(prefHeight, maxHeight))
        x, y = self._parent.GetSize()
        return wx.Size(x, -1)


    def OnLeftDown(self, evt):
        # do the combobox selection
        index = self.lb.HitTest(evt.GetPosition())

        if index < 0:
            evt.Skip()
            return

        label = self.lb.GetString(index)

        if label in self.value:
            i = self.value.index(label)
            self.value.pop(i)

        else:
            self.value.append(label)

        self._parent.SetValue(','.join(self.value))
        self.lb.SetCheckedStrings(self.value)

        if self.on_change:
            e = wx.CommandEvent(wx.EVT_TEXT.evtType[0], self._parent.GetId())
            e.SetString(label)
#            e.SetClientData('3')
            self._parent.Command(e)

class BaseProperty():
    def __init__(self, name, default_value, value, is_modified,
                 is_editable, validator,
                 on_change, button):

        self.name = name
        self.default_value = default_value
        self.value = value
        self.is_modified = is_modified
        self.is_editable = is_editable
        self.validator = validator
        self.on_change = on_change
        self.button = button

    def __str__(self):
        modified = '*' if self.is_modified else ''
        return '<%s %s%s: %s at %x>' % (self.__class__.__name__,
                    self.name, modified, self.value, id(self))

    def __repr__(self):
        return str(self)

class ChooseProperty(BaseProperty):
    def __init__(self, name, default_value, value, is_modified=False,
                 is_editable=True, validator=None,
                 on_change=None, button=None, is_multi=False):

        for dv in default_value:
            if not isinstance(dv, basestring):
                index = default_value.index(dv)
                default_value[index] = repr(dv)

        value = str(value)
        BaseProperty.__init__(self, name, default_value, value, is_modified,
                              is_editable, validator,
                              on_change, button)
        self.is_multi = is_multi

class TextProperty(BaseProperty):
    def __init__(self, name, default_value, value, is_modified=False,
                 is_editable=True, validator=None,
                 on_change=None, button=None):

        BaseProperty.__init__(self, name, default_value, value, is_modified,
                              is_editable, validator,
                              on_change, button)

class ToggleProperty(BaseProperty):
    def __init__(self, name, default_value, value, is_modified=False,
                 is_editable=True, validator=None,
                 on_change=None, button=None):

        BaseProperty.__init__(self, name, default_value, value, is_modified,
                              is_editable, validator,
                              on_change, button)

class RangeProperty(BaseProperty):
    def __init__(self, name, default_value, value, is_modified=False,
                 is_editable=True, validator=None,
                 on_change=None, button=None):

        BaseProperty.__init__(self, name, default_value, value, is_modified,
                              is_editable, validator,
                              on_change, button)

class SeedProperty(BaseProperty):
    def __init__(self, name, default_value, value, is_modified=False,
                 is_editable=True, validator=None,
                 on_change=None, button=None):

        BaseProperty.__init__(self, name, default_value, value, is_modified,
                              is_editable, validator,
                              on_change, button)

class PropertyWidget(wx.Panel):
    def __init__(self, parent, properties, _id=-1, size=wx.DefaultSize,
                 pos=wx.DefaultPosition):
        wx.Panel.__init__(self, parent, _id, size=size, pos=pos)

        self.parent = parent

        self.Hide()
        self.Freeze()

        # rows, cols, vgap, hgap
        self.sizer = wx.FlexGridSizer(len(properties), 2, 1, 1)
        self.SetSizer(self.sizer)
        self.sizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.sizer.AddGrowableCol(1, 1)
        
        self.prop_list = []
        self.prop_map = {}
        self.seed_map = {}
        self.changes = {}

        for prop in properties:

            label = wx.StaticText(self, -1, prop.name, size=(100, -1), )
            label.SetBackgroundColour('White')
            propctrl = None

            if isinstance(prop, ChooseProperty):
                propctrl = self.make_choose_ctrl(prop, self.on_change)
                self.Bind(wx.EVT_TEXT, self.on_change, propctrl)
                if prop.is_modified:
                    propctrl.SetBackgroundColour(MOD_COLOR)
                self.prop_map[propctrl] = prop

            elif isinstance(prop, TextProperty):
                propctrl = self._make_text(prop.value, prop.is_editable)
                
                self.Bind(wx.EVT_TEXT, self.on_change, propctrl)
                if prop.is_modified:
                    propctrl.SetBackgroundColour(MOD_COLOR)
                self.prop_map[propctrl] = prop

            elif isinstance(prop, ToggleProperty):
                propctrl = wx.CheckBox(self, -1, '')
                propctrl.SetValue(prop.value)
                if not prop.is_editable:
                    propctrl.Enable(False)

                self.Bind(wx.EVT_CHECKBOX, self.on_change, propctrl)
                if prop.is_modified:
                    propctrl.SetBackgroundColour(MOD_COLOR)
                self.prop_map[propctrl] = prop

            elif isinstance(prop, RangeProperty):
#                propctrl = RangeCtrl(self, prop)
                if isinstance(prop.value, float):
                    prop.value = str(round(prop.value, 3))
                else:
                    prop.value = str(prop.value)

                propctrl = self._make_text(prop.value, prop.is_editable)
                
                self.Bind(wx.EVT_TEXT, self.on_change, propctrl)
                if prop.is_modified:
                    propctrl.SetBackgroundColour(MOD_COLOR)
                self.prop_map[propctrl] = prop

            elif isinstance(prop, SeedProperty):
#                propctrl = RangeCtrl(self, prop, seed=True)
                prop.value = str(prop.value)
                propctrl = wx.BoxSizer(wx.HORIZONTAL)

                txt_ctrl = self._make_text(prop.value, prop.is_editable)

                self.Bind(wx.EVT_TEXT, self.on_change, txt_ctrl)

                if prop.is_modified:
                    txt_ctrl.SetBackgroundColour(MOD_COLOR)
                self.prop_map[txt_ctrl] = prop

                s = (16, 16)
                L = lambda x: load_image(app_abs_path('icons', x + '.png'), s)
                st = platebtn.PB_STYLE_DEFAULT
                pb = platebtn.PlateButton

                proc_btn = pb(self, wx.ID_ANY, '', L('procodile'), style=st)

                proc_btn.SetToolTipString("Generate random seed")
                self.seed_map[proc_btn] = txt_ctrl
                self.Bind(wx.EVT_BUTTON, self.on_proc, proc_btn)

                propctrl.Add(txt_ctrl, 1, wx.ALIGN_RIGHT|wx.EXPAND)
                propctrl.Add(proc_btn, 0, wx.ALIGN_RIGHT)

            else:
                log.warning('unsupported property')

            self.prop_list.append((label, 0, wx.EXPAND))
            self.prop_list.append((propctrl, 1, wx.EXPAND))

        self.sizer.AddMany(self.prop_list)
        self.sizer.Layout()
        self.Thaw()

    def _make_text(self, value, is_editable):
        s = wx.BORDER_NONE if is_editable else wx.BORDER_NONE|wx.TE_READONLY
        return wx.TextCtrl(self, -1, value, style=s)

    def on_proc(self, event):
        btn = event.GetEventObject()
        txt_ctrl = self.seed_map[btn]
        seed = random.randint(0, 65535)
        txt_ctrl.SetValue(str(seed))

    def on_change(self, event):
        propctrl = event.GetEventObject()
        if isinstance(propctrl, wx.CheckListBox):
            propctrl = propctrl.parent

        prop = self.prop_map[propctrl]

        if prop.value != propctrl.GetValue():
            self.changes[prop.name] = propctrl.GetValue()

            propctrl.SetBackgroundColour(MOD_COLOR)

        else:
            if prop.name in self.changes:
                del self.changes[prop.name]

            propctrl.SetBackgroundColour("White")

        if prop.on_change:
            prop.on_change(propctrl.GetValue())

    def get_changes(self):
        for propctrl, prop in self.prop_map.iteritems():
            if prop.is_modified:
                self.changes[prop.name] = propctrl.GetValue()

        return self.changes

    def make_choose_ctrl(self, prop, on_change=None):
        if prop.is_multi:
            propctrl = wx.combo.ComboCtrl(self,
                                          style=wx.CB_READONLY|wx.BORDER_NONE,
                                          size=(122, -1))
            checklist = CheckListComboPopup(propctrl,
                                            prop.default_value, on_change)
            propctrl.SetPopupControl(checklist)

            if prop.value:
                checklist.SetValue(prop.value)
                propctrl.SetValue(prop.value)
                
        else:
            style = wx.BORDER_NONE if prop.is_editable\
                        else wx.BORDER_NONE|wx.TE_READONLY
            propctrl = wx.ComboBox(self, -1, prop.value,
                                   choices=prop.default_value,
                                   style=style)
        return propctrl

class RangeCtrl(wx.Panel):
    def __init__(self, parent, prop, seed=False):
        wx.Panel.__init__(self, parent)

        self._parent = parent
        self.prop = prop
        min, max = self.prop.default_value
        value = self.prop.value
        self.prop.value = round(value, 3) if value else None
        
        self.Freeze()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.propctrl = wx.BoxSizer(wx.HORIZONTAL)

        if isinstance(min, float):
            self.property1 = FS.FloatSpin(self, -1, min_val=min,
                                     max_val=max, increment=0.001,
                                     value=self.prop.value or min)
            self.property1.SetDigits(3)

            self.property1.old_value = self.prop.value or min
            self.property1.new_value = self.prop.value or min

            self.Bind(FS.EVT_FLOATSPIN, self.on_floatspin_change,
                                                                self.property1)
            if self.prop.is_modified:
                self.property1.GetTextCtrl().SetBackgroundColour(MOD_COLOR)

            self.property2 = FS.FloatSpin(self, -1, min_val=min,
                                     max_val=max, increment=0.001,
                                     value=self.prop.value or max)
            self.property2.SetDigits(3)

            self.property2.old_value = self.prop.value or max
            self.property2.new_value = self.prop.value or max

            self.Bind(FS.EVT_FLOATSPIN, self.on_floatspin_change,
                                                                self.property2)
            if self.prop.is_modified:
                self.property2.GetTextCtrl().SetBackgroundColour(MOD_COLOR)

        else:
            self.property1 = wx.SpinCtrl(self, -1, str(self.prop.value or min))
            self.property1.SetRange(min, max)
            self.Bind(wx.EVT_SPINCTRL, self.on_change, self.property1)
            if self.prop.is_modified:
                self.property1.SetBackgroundColour(MOD_COLOR)

            self.property2 = wx.SpinCtrl(self, -1, str(self.prop.value or max))
            self.property2.SetRange(min, max)
            self.Bind(wx.EVT_SPINCTRL, self.on_change, self.property2)
            if self.prop.is_modified:
                self.property2.SetBackgroundColour(MOD_COLOR)

            if seed:
                img_path = app_abs_path('icons', 'procodile.png')
                bmp = load_image(img_path, (16,10))
                proc_btn = wx.BitmapButton(self, -1, bmp, (5, 5),
                               (bmp.GetWidth(), bmp.GetHeight()))
                proc_btn.SetToolTipString("Select random seed")

                self.propctrl.Add(proc_btn, 0, wx.ALIGN_RIGHT)
                self.Bind(wx.EVT_BUTTON, self.on_proc, proc_btn)

        self.propctrl.Add(self.property1, 1, wx.EXPAND)
        self.propctrl.Add(self.property2, 1, wx.EXPAND)
        self.sizer.Add(self.propctrl, 1, wx.EXPAND)
        self.sizer.Layout()
        self.Thaw()
            
    def on_floatspin_change(self, event):
        propctrl = event.GetEventObject()

        propctrl.old_value = propctrl.new_value
        propctrl.new_value = propctrl.GetValue()

        if propctrl.old_value != propctrl.new_value:
            self.on_change(event)

    def on_change(self, event):
        ctrl = event.GetEventObject()
        new_values = (self.property1.getvalue(), self.property2.getvalue())
        actual_values = (self.prop.value, self.prop.value)

        if actual_values != new_values():
            self._parent.changes[self.prop.name] = (
                                                    self.property1.getvalue(),
                                                    self.property2.getvalue()
                                                    )
        elif self.prop.name in self._parent.changes:
            del self._parent.changes[self.prop.name]

        if self.prop.value != ctrl.GetValue():
            if isinstance(ctrl, FS.FloatSpin):
                ctrl.GetTextCtrl().SetBackgroundColour(MOD_COLOR)
            else:
                ctrl.SetBackgroundColour(MOD_COLOR)

        else:
            if isinstance(ctrl, FS.FloatSpin):
                ctrl.GetTextCtrl().SetBackgroundColour("White")
            else:
                ctrl.SetBackgroundColour("White")

        if self.prop.on_change:
            self.prop.on_change(ctrl.GetValue())

    def on_proc(self, event):
        #TODO CHECK FOR PROC RETURNING DEFAULT VALUES
        seed = random.randint(0, 65535)
        self.property1.SetValue(seed)
        self.property2.SetValue(seed)

        self._parent.changes[self.prop.name] = (seed, seed)
        spins = [spin1, spin2]

        for spin in spins:
            if self.prop.value != spin.GetValue():
                spin.SetBackgroundColour(MOD_COLOR)

            else:
                spin.SetBackgroundColour("White")

            if self.prop.on_change:
                self.prop.on_change((seed, seed))
