import copy
import logging

import wx
import wx.html
import  wx.lib.wxpTag
import  wx.lib.scrolledpanel as scrolled
import wx.lib.platebtn as platebtn
import wx.lib.agw.customtreectrl as CT
import wx.lib.agw.pycollapsiblepane as PCP

from procodile.utils import log_method_call as logmt
from procodile.utils import log_function_call as logfn
from procodile.loader import get_class
from procodile.recipe import RecipeBasedGenerator

from utils import load_image, app_abs_path
from utils import ChooseProperty, TextProperty, ToggleProperty, RangeProperty
from utils import SeedProperty, PropertyWidget
import utils
from dialogs import get_generator_info

log = logging.getLogger()

class ConfGeneratorDialog(wx.Dialog):
    '''
    Dialog to add or edit generator item in generators
    list of recipe configuration
    '''

    def __init__(self, parent, _id,
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE,
                 generator_info=None):

        title = 'Edit Generator' if generator_info else 'Add Generator'

        wx.Dialog.__init__(self, parent, _id, title, size=size, pos=pos,
                            style=style)

        s = self
        g = generator_info
        s.name, s.uri, s.id, s.version = g if g else [''] * 4

        self.texts = {}

        self.okay_button = None
        self.cancel_button = None

        self.Freeze()

        self._make_buttons()
        self._layout()

        self.Thaw()

    def _make_buttons(self):

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        self.okay_button = btn

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("Cancel selection and close dialog")
        self.cancel_button = btn

    def _layout(self):

        sz = wx.BoxSizer(wx.VERTICAL)
        gs = wx.GridSizer(4, 2, 2, 2)  # rows, cols, vgap, hgap

        for index, (field, attr) in enumerate((
                      ('Name', 'name'),
                      ('URI', 'uri'),
                      ('Id', 'id'),
                      ('Version', 'version'))):

            value = getattr(self, attr) or ''
            label = wx.StaticText(self, -1, field, size=(75, -1))
            text = wx.TextCtrl(self, -1, value, size=(150,-1))
            self.texts[text] = attr
            self.Bind(wx.EVT_TEXT, self.OnTextEvent, text)

            gs.Add(label, 0, wx.EXPAND, 10)
            gs.Add(text, 0, wx.EXPAND, 10)

            if index == 0:
                text.SetFocus()

        gs.Layout()
        sz.Add(gs, 0, wx.EXPAND, 10)

        bs = wx.BoxSizer()
        bs.Add(self.okay_button, 0)
        bs.Add(self.cancel_button, )
        bs.Layout()

        sz.Add(bs, 0, wx.ALIGN_RIGHT, 10)

        self.SetSizer(sz)
        sz.Fit(self)
        sz.Layout()

    def get_info(self):
        return [self.name, self.uri, self.id, self.version]

    def OnTextEvent(self, event):
        text = event.GetEventObject()
        attr = self.texts[text]
        value = event.GetString()
        setattr(self, attr, value)

class ModificationsWidget(wx.Panel):
    def __init__(self, parent, doc):
        wx.Panel.__init__(self, parent)

        self.doc = doc
        self.recipe = doc.recipe
        self.root = None
        self.add_match_node = None
        self.mod_no = 0

        self.Freeze()

        self.widget = CT.CustomTreeCtrl(self, wx.ID_ANY, wx.DefaultPosition,
                                wx.DefaultSize,
                                wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | \
                                wx.TR_SINGLE | wx.TR_EDIT_LABELS | \
                                wx.TR_NO_LINES)
                                
        self._image_list = None
        self._image_indices = {}
        self._init_tree_images()

        w = self.widget
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemFocus, w)
#        self.Bind(wx.EVT_TREE_KEY_DOWN, self.OnModFocus, w)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnLabelEditStart, w)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnLabelEditEnd, w)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(self.widget, 1, wx.EXPAND)

        #: buttons
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        s = (16, 16)
        L = lambda x: load_image(app_abs_path('icons', x + '.png'), s)
        st = platebtn.PB_STYLE_DEFAULT
        pb = platebtn.PlateButton

        self.mod_button = pb(self, wx.ID_ANY, '', L('c_mod_n'), style=st)
        self.condition_button = pb(self, wx.ID_ANY, '', L('c_condition_n'), style=st)
        self.action_button = pb(self, wx.ID_ANY, '', L('c_action_n'), style=st)
        self.edit_button = pb(self, wx.ID_ANY, '', L('c_edit'), style=st)
        self.del_button = pb(self, wx.ID_ANY, '', L('c_del'), style=st)
        self.up_button = pb(self, wx.ID_ANY, '', L('c_up'), style=st)
        self.down_button = pb(self, wx.ID_ANY, '', L('c_down'), style=st)

        self.Bind(wx.EVT_BUTTON, self.OnModButton, self.mod_button)
        self.Bind(wx.EVT_BUTTON, self.OnConditionButton, self.condition_button)
        self.Bind(wx.EVT_BUTTON, self.OnActionButton, self.action_button)
        self.Bind(wx.EVT_BUTTON, self.OnEditButton, self.edit_button)
        self.Bind(wx.EVT_BUTTON, self.OnDelButton, self.del_button)
        self.Bind(wx.EVT_BUTTON, self.OnUpButton, self.up_button)
        self.Bind(wx.EVT_BUTTON, self.OnDownButton, self.down_button)

        self.button_sizer.Add(self.mod_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.condition_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.action_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.edit_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.del_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.up_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.down_button, 0, wx.ALIGN_RIGHT)

        self.button_sizer.Layout()

        self.sizer.Add(self.button_sizer, 0, wx.ALIGN_RIGHT)

        self.sizer.Layout()

        self.Thaw()
        
        self.fill()

    def _init_tree_images(self):
        size = (16,16)
        images = wx.ImageList(*size)

        L = lambda x: load_image(app_abs_path('icons', x + '.png'), size)

        self._image_indices['modification'] = images.Add(L('c_mod'))
        self._image_indices['add_mod'] = images.Add(L('c_mod_n'))
        self._image_indices['condition'] = images.Add(L('c_condition'))
        self._image_indices['action'] = images.Add(L('c_action'))

        self._images_list = images
        self.widget.SetImageList(images)

    def _set_node_image(self, node, image):
        index = self._image_indices[image]
        self.widget.SetItemImage(node, index, wx.TreeItemIcon_Normal)
        self.widget.SetItemImage(node, index, wx.TreeItemIcon_Expanded)

    def OnItemFocus(self, evt):
        item = self.widget.GetSelection()
        if item:
            if self.widget.GetItemText(item) == '...':
                self.OnModButton(evt)
                return

            self.widget.EditLabel(item)

        w = self.widget

        item = self.widget.GetSelection()
        pydata = w.GetPyData(item)

        if not pydata:
            return

        item_type, data = pydata

        if item_type == 'match':
            _children = self._get_children(item)
            for cc in _children:
                item_type, data = w.GetPyData(cc)

                if item_type == 'condition':
                    match, condition = data
                    self.doc.select_xpath(condition)

    def get_nxt_modname(self):
        self.mod_no += 1
        setname = 'Mod%s' % self.mod_no
        if setname in self.recipe.matches:
            return self.get_nxt_modname()

        return setname

    def fill(self):
        matches = self.recipe.matches

        w = self.widget
        self.root = w.AddRoot('Modifications')

        self.mod_no = len(matches)
        for i, match in enumerate(matches):
            match_name = match[0]
            conditions = match[1:]
            actions = self.recipe.get_onmatch(match_name)[1:]

            mnode = w.AppendItem(self.root, match_name)
            self._set_node_image(mnode, 'modification')
            w.SetPyData(mnode, ('match', match_name))

            for c in conditions:
                cond_node = w.AppendItem(mnode, c)
                self._set_node_image(cond_node, 'condition')
                w.SetPyData(cond_node, ('condition', (match_name, c)))

            for k,v in actions:
                kv_node = w.AppendItem(mnode, self._make_disp_string(k, v))
                self._set_node_image(kv_node, 'action')
                w.SetPyData(kv_node, ('kv', (match_name, [k,v])))

        add_node = w.AppendItem(self.root, '...')
        self._set_node_image(add_node, 'add_mod')
        w.SetPyData(add_node, ('addmatch', None))
        self.add_match_node = add_node

    def _make_disp_string(self, k, v):
        return '%s = %s' % (k, v)

    def refresh(self):
        self.widget.DeleteAllItems()
        self.fill()

    def _get_selected_item(self):
        item = self.widget.GetSelection()
        if not item:
            return

        return item, self.widget.GetItemPyData(item)

    def _get_value(self, title, prompt, value):
        dlg = wx.TextEntryDialog(self, prompt, title, value)

        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue()

        dlg.Destroy()
        return value

    def add_actions(self, node, match, changes):
        w = self.widget
        
        for key, value in changes:
            value = value if isinstance(value, basestring) else str(value)
            action = key+'='+value
            kv_node = w.AppendItem(node, action)
            self._set_node_image(kv_node, 'action')
            w.SetPyData(kv_node, ('kv', (match, [key, value])))
            self.recipe.add_kv_pair(match, key, value)

    def _del_existing_mod(self, xpath):
        w = self.widget
        name = None

        children = self._get_deep_children(self.root)
        for c in children:
            if not w.GetPyData(c):
                continue

            item_type, data = w.GetPyData(c)
            if item_type == 'condition':
                match, condition = data
                if condition == xpath:
                    mnode = c.GetParent()
                    name = w.GetItemText(mnode)
                    w.Delete(mnode)
                    self.recipe.del_match(match)
                    self.recipe.del_onmatch(match)

        return name

    def update_modification(self, changes, xpath, mod_name=None):
        w = self.widget
        exist_mod_name = self._del_existing_mod(xpath)

        if not changes:
            return
        
        match = exist_mod_name or mod_name or self.get_nxt_modname()
        prev_node = w.GetPrevSibling(self.add_match_node)
        if prev_node:
            mnode = w.InsertItem(self.root, prev_node, match)
        else:
            mnode = w.PrependItem(self.root, match)

        self._set_node_image(mnode, 'modification')
        w.SetPyData(mnode, ('match', match))
        self.recipe.add_match(match)
        self.recipe.add_onmatch(match)

        cond_node = w.AppendItem(mnode, xpath)
        self._set_node_image(cond_node, 'condition')
        w.SetPyData(cond_node, ('condition', (match, xpath)))
        self.recipe.add_condition(match, xpath)

        self.add_actions(mnode, match, changes)

        w.Expand(mnode)
        self.widget.EnsureVisible(mnode)
        self.widget.EditLabel(mnode)

    def OnModButton(self, event):
        w = self.widget

        match = self.get_nxt_modname()
        prev_node = w.GetPrevSibling(self.add_match_node)
        if prev_node:
            mnode = w.InsertItem(self.root, prev_node, match)
        else:
            mnode = w.PrependItem(self.root, match)

        self._set_node_image(mnode, 'modification')
        w.SetPyData(mnode, ('match', match))
        self.recipe.add_match(match)
        self.recipe.add_onmatch(match)

        cond_node = w.AppendItem(mnode, 'condition')
        self._set_node_image(cond_node, 'condition')
        w.SetPyData(cond_node, ('condition', (match, 'condition')))
        
        kv_node = w.AppendItem(mnode, 'action')
        self._set_node_image(kv_node, 'action')
        w.SetPyData(kv_node, ('kv', (match, ['key', 'value'])))

        w.Expand(mnode)
        self.widget.EnsureVisible(mnode)
        self.widget.EditLabel(mnode)

    def OnConditionButton(self, event):
        item, data = self._get_selected_item()
        if not data:
            return

        w = self.widget
        child = w.GetLastChild(item)
        while child:
            if w.GetItemText(child) == 'condition':
                self.widget.EnsureVisible(child)
                self.widget.EditLabel(child)
                return
            child = w.GetPrevSibling(child)

        parent = w.GetItemParent(item)
        if parent != self.root:
            return

        match = w.GetItemText(item)
        m = self.recipe.get_match(match)
        index = len(m[1:])

        cond_node = w.InsertItem(item, index, 'condition')

        self._set_node_image(cond_node, 'condition')
        w.SetPyData(cond_node, ('condition', (match, 'condition')))

        self.widget.EnsureVisible(cond_node)
        self.widget.EditLabel(cond_node)
        
    def OnActionButton(self, event):
        item, data = self._get_selected_item()
        if not data:
            return

        w = self.widget
        child = w.GetLastChild(item)
        while child:       
            if w.GetItemText(child) == 'action':
                w.EnsureVisible(child)
                w.EditLabel(child)
                return
            child = w.GetPrevSibling(child)

        parent = w.GetItemParent(item)
        if parent != self.root:
            return

        kv_node = w.AppendItem(item, 'action')
        self._set_node_image(kv_node, 'action')
        w.SetPyData(kv_node, ('kv', (w.GetItemText(item), ['key', 'value'])))

        w.EnsureVisible(kv_node)
        w.EditLabel(kv_node)

    def OnDelButton(self, event):
        w = self.widget

        data = self._get_selected_item()
        item, pyobj = data
        
        if item == self.root:
            return

        item_type, data = pyobj

        if item_type == 'match':
            w.Delete(item)
            match = data
            self.recipe.del_match(match)
            self.recipe.del_onmatch(match)

        elif item_type == 'condition':
            w.Delete(item)
            match, condition = data
            self.recipe.del_condition(match, condition)

        elif item_type == 'kv':
            w.Delete(item)
            onmatch, kv = data
            self.recipe.del_kv_pair(onmatch, *kv)

    def OnEditButton(self, event):
        item = self.widget.GetSelection()
        if item == self.root:
            return
        else:
            self.widget.EditLabel(item)

    def OnLabelEditStart(self, evt):
        label = evt.GetItem().GetText()
#        if label == 'condition' or label == 'action':
#            evt.GetItem().SetText('')

    def _get_children(self, item):
        children = []
        w = self.widget
        child = w.GetLastChild(item)
        while child:
            children.append(child)
            child = w.GetPrevSibling(child)
        return children

    def _get_deep_children(self, item):
        children = []
        w = self.widget
        child = w.GetLastChild(item)
        while child:
            children.append(child)
            children.extend(self._get_children(child))
            child = w.GetPrevSibling(child)
        return children

    def OnLabelEditEnd(self, evt):
#        item = evt.GetItem()
#        if self.widget.GetItemText(item) == 'condition' or 'action':
#            if not evt.GetLabel():
#                wx.CallAfter(self.widget.Delete, item)
#                return

        if evt.IsEditCancelled():
            return

        w = self.widget
        item = evt.GetItem()
        pyobj = w.GetItemPyData(item)
        
        if w.GetItemText(item) == evt.GetLabel():
            return
        
        if not pyobj:
            return

        item_type, data = pyobj

        if item_type == 'match':

            new_match = evt.GetLabel()
            if not new_match:
                return

            w.SetPyData(item, ('match', new_match))

            if not self.recipe.get_match(data):
                self.recipe.add_match(new_match)
                self.recipe.add_onmatch(new_match)
                return

            self.recipe.rename_match(data, new_match)
            self.recipe.rename_onmatch(data, new_match)

            # adjust data of all child nodes
            children = self._get_children(item)
            for c in children:
                item_type, (old_match, condition) = w.GetPyData(c)
                w.SetPyData(c, (item_type, (new_match, condition)))

        elif item_type == 'condition':
            match, old_condition = data

            condition = evt.GetLabel()
            if not condition:
                w.Delete(item)
                self.recipe.del_condition(match, old_condition)
                return

            w.SetPyData(item, ('condition', (match, condition)))

            if old_condition == 'condition':
                self.recipe.add_condition(match, condition)
                return
            
            self.recipe.change_condition(match, old_condition, condition)

        elif item_type == 'kv':
            onmatch, old_kv = data

            if not evt.GetLabel():
                w.Delete(item)
                self.recipe.del_kv_pair(onmatch, *old_kv)
                return
           
            # ensure that user has entered in correct format
            label = evt.GetLabel()
            if not ('=' in label and len(label.split('=')) == 2):
                evt.Veto()
                return

            key, value = evt.GetLabel().split('=')

            w.SetPyData(item, ('kv', (onmatch, [key, value])))

            if old_kv == ['key', 'value']:
                self.recipe.add_kv_pair(onmatch, key, value)
                return

            self.recipe.change_kv_pair(onmatch, old_kv, [key, value])

    def OnUpButton(self, event):
        import pprint
        pprint.pprint(self.recipe.data)

    def OnDownButton(self, event):
        pass

def get_children(_class, name, children=None):
    children = children if children is not None else {}

    sub_gens = _class.get_subgens()

    gens_to_call = []

    for key, value in sub_gens.iteritems():
        if value in children.values():
            continue

        gens_to_call.append((key, value))

        if key in children:
            key = name + '.' + key

        i = 1
        while key in children:
            key = key + str(i)
            i += 1

        children[key] = value

    for alias, sg in gens_to_call:
        get_children(sg, alias, children)

    return children

class GeneratorsWidget(wx.Panel):
    def __init__(self, parent, doc):
        wx.Panel.__init__(self, parent)

        self.app = doc.app
        self.recipe = doc.recipe
        self.root = None
        self.generators = []

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.Freeze()

        self.widget = CT.CustomTreeCtrl(self, wx.ID_ANY, wx.DefaultPosition,
                            wx.DefaultSize,
                            wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | \
                            wx.TR_SINGLE |wx.TR_NO_LINES | wx.TR_NO_BUTTONS)
        self.widget.SetIndent(-10)

        self.sizer.Add(self.widget, 1, wx.EXPAND)

        self._image_list = None
        self._image_indices = {}
        self._init_tree_images()

        w = self.widget
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnItemFocus, w)

        #: buttons
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        s = (16, 16)
        L = lambda x: load_image(app_abs_path('icons', x + '.png'), s)
        st = platebtn.PB_STYLE_DEFAULT
        pb = platebtn.PlateButton

        self.add_button = pb(self, wx.ID_ANY, '', L('c_add'), style=st)
        self.edit_button = pb(self, wx.ID_ANY, '', L('c_edit'), style=st)
        self.del_button = pb(self, wx.ID_ANY, '', L('c_del'), style=st)
        self.up_button = pb(self, wx.ID_ANY, '', L('c_up'), style=st)
        self.down_button = pb(self, wx.ID_ANY, '', L('c_down'), style=st)

        self.Bind(wx.EVT_BUTTON, self.OnAddButton, self.add_button)
        self.Bind(wx.EVT_BUTTON, self.OnEditButton, self.edit_button)
        self.Bind(wx.EVT_BUTTON, self.OnDelButton, self.del_button)
        self.Bind(wx.EVT_BUTTON, self.OnUpButton, self.up_button)
        self.Bind(wx.EVT_BUTTON, self.OnDownButton, self.down_button)

        self.button_sizer.Add(self.add_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.edit_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.del_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.up_button, 0, wx.ALIGN_RIGHT)
        self.button_sizer.Add(self.down_button, 0, wx.ALIGN_RIGHT)

        self.button_sizer.Layout()

        self.sizer.Add(self.button_sizer, 0, wx.ALIGN_RIGHT)

        self.sizer.Layout()

        self.Thaw()

        self.fill()

    def _init_tree_images(self):
        size = (16,16)
        images = wx.ImageList(*size)

        L = lambda x: load_image(app_abs_path('icons', x + '.png'), size)

        self._image_indices['generator'] = images.Add(L('generator_icon'))

        self._images_list = images
        self.widget.SetImageList(images)

    def _set_node_image(self, node, image):
        index = self._image_indices[image]
        self.widget.SetItemImage(node, index, wx.TreeItemIcon_Normal)
        self.widget.SetItemImage(node, index, wx.TreeItemIcon_Expanded)

    def OnItemFocus(self, evt):
        item = self.widget.GetSelection()
        if item:
            self.edit_selected_item()

    def fill(self):
        self.root = self.widget.AddRoot('Generators')
        gens = self.recipe.generators

        for gen in gens:
            name, uri, _id, version = gen
            self.generators.append(name)
            gnode = self.widget.AppendItem(self.root, name)
            self._set_node_image(gnode, 'generator')
            self.widget.SetPyData(gnode, gen)

        root_name, root_uri, root_id, root_version = self.recipe.generator
        root_class = get_class(root_uri, root_id, root_version)

        children = get_children(root_class, root_id)

        for name, child in children.iteritems():
            ident = child.IDENT
            
            if name in self.generators:
                continue

            self.generators.append(name)
            gnode = self.widget.AppendItem(self.root, name)
            self._set_node_image(gnode, 'generator')

            gen_data = (name, ident.location, ident.id, ident.version)
            self.recipe.add_generator(*gen_data)
            self.widget.SetPyData(gnode, gen_data)

    def refresh(self):
        self.widget.Clear()
        self.fill()

    def _display_dialog(self, gen):
        dlg = ConfGeneratorDialog(self, -1, generator_info=gen)
        dlg.CenterOnParent()
        response = dlg.ShowModal()

        if response == wx.ID_CANCEL:
            return

        return dlg.get_info()

    def validate_data(self, gen):
        if not gen:
            return False

        name, uri, _id, version = gen
        return False if not name or not uri or not _id else True

    def OnAddButton(self, event):
        g_info = get_generator_info(self, self.app, display_name=True)
        if not g_info:
            return

        is_remote, name, package_dir, repo_uri, generator_id, ver = g_info
        name = name or generator_id.rsplit('.')[-1]
        repo_uri = repo_uri or package_dir

        gen = name, repo_uri, generator_id, ver

        if not self.validate_data(gen):
            return

        name, uri, _id, version = gen

        gnode = self.widget.AppendItem(self.root, name)
        self.widget.SetPyData(gnode, gen)
        self._set_node_image(gnode, 'generator')

        self.recipe.add_generator(name, uri, _id, version)

    def OnEditButton(self, event):
        self.edit_selected_item()

    def OnUpButton(self, event):
        pass

    def OnDownButton(self, event):
        pass

    def OnListEvent(self, event):
        pass

    def OnListDoubleClick(self, event):
        self.edit_selected_item()

    def OnDelButton(self, event):
        item = self.widget.GetSelection()
        if item == self.root:
            return

        self.widget.Delete(item)
        self.recipe.del_generator(self.widget.GetItemText(item))

    def edit_selected_item(self):
        w = self.widget
        item = w.GetSelection()
        if item == self.root:
            return

#        gen = self.recipe.get_generator(w.GetItemText(item))
        gen = w.GetPyData(item)
        old_name, old_uri, old_id, old_version = gen

        g_info = get_generator_info(self, self.app, gen, display_name=True)
        if not g_info:
            return

        is_remote, name, package_dir, repo_uri, generator_id, ver = g_info

        name = name or generator_id.rsplit('.')[-1]
        repo_uri = repo_uri or package_dir

        gen = name, repo_uri, generator_id, ver

        if not self.validate_data(gen):
            return

        name, uri, _id, version = gen

        if name != old_name:
            self.recipe.rename_generator(old_name, name)

        self.recipe.change_generator(name, uri, _id, version)

        w.SetItemText(item, name)
        w.SetPyData(item, gen)

class ConfigurationWidget(scrolled.ScrolledPanel):
    def __init__(self, parent, doc):
        scrolled.ScrolledPanel.__init__(self, parent, size=wx.DefaultSize)

        self.panes = {}
        self.doc = doc
        self.gen_widget = doc.gen_widget
        self.mod_widget = doc.mod_widget
        self.detail_panes = []
        self.prop_panes = []
        self.xpath = None
        self.node = None
        
        self.Freeze()

        self.apply_btn = wx.Button(self, wx.ID_ANY, 'Apply')
        self.apply_btn.SetHelpText('Apply modifications')
        self.apply_btn.SetDefault()
        self.apply_btn.Hide()
        self.Bind(wx.EVT_BUTTON, self.on_apply, self.apply_btn)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(self.apply_btn, 0, wx.EXPAND)

        _panes = [('Generators', self.gen_widget),
                  ('Modifications', self.mod_widget)
                 ]

        pypanes = self.add_panes(_panes)
        for pane in pypanes:
            pane.Show()

        self.sizer.Layout()
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.Thaw()

    @logmt
    def on_apply(self, event, on_first_gen_created=None):
        changes = []

        for pname, ppane in self.prop_panes:
            pchanges = ppane.get_changes()
            pchanges = [('config.'+key, value) for key, value in
                                                        pchanges.iteritems()]
            changes.extend(pchanges)

        for dname, dpane in self.detail_panes:
            dchanges = dpane.get_changes()

            if 'Seed' in dchanges:
                changes.append(('s_seed', dchanges['Seed']))

            if 'Deep Seed' in dchanges:
                changes.append(('seed', dchanges['Deep Seed']))

            if 'Replace with' in dchanges:
                changes.append(('generator', dchanges['Replace with']))
                
            if 'Generate' in dchanges:
                if not dchanges['Generate']:
                    changes.append(('generator', None))

        self.mod_widget.update_modification(changes, self.xpath)
        if changes:
            gen_infos = self.doc.query(self.xpath)
            if gen_infos:
                self.doc.rebuild(gen_infos, on_first_gen_created)

    def on_first_gen_created(self, node):
        curr_node, curr_type = self.node
        self.update_panes(node, curr_type, self.xpath)

    @logmt
    def update_panes(self, node, type, xpath):
        self.xpath = xpath
        self.node = (node, type)
        self.Freeze()
        detail_pane = self.get_detail_pane(node, type, self.xpath)
        detail_pypanes = self.add_details(detail_pane)
        
        property_pane = self.get_property_pane(node, type) if type != 'geom'\
                                                           else []
        property_pypanes = self.add_properties(property_pane)

        # Apply button
        self.apply_btn.Hide()
        success = self.sizer.Detach(self.apply_btn)
        if not success:
            log.warning('detachment of apply btn failed in conf_widget')

        self.sizer.Add(self.apply_btn, 0, wx.ALL|wx.ALIGN_RIGHT, 10)
        self.apply_btn.Show()

        for pane in detail_pypanes:
            pane.Expand()
            pane.Show()

        for pane in property_pypanes:
            pane.Expand()
            pane.Show()

        self.sizer.Layout()
        self.Thaw()

    def add_details(self, detail_panes):
        self.hide_panes(self.detail_panes)
        pypanes = self.add_panes(detail_panes)
        self.detail_panes = detail_panes
        return pypanes

    def add_properties(self, prop_panes):
        self.hide_panes(self.prop_panes)
        pypanes = self.add_panes(prop_panes)
        self.prop_panes = prop_panes
        return pypanes
        
    def populate_panel(self, panel, widget):
        pane = panel.GetPane()
        widget.Reparent(pane)

        sizer = wx.BoxSizer(wx.VERTICAL)
        pane.SetSizer(sizer)
        sizer.Add(widget, 1, wx.EXPAND)
        sizer.Layout()

    def add_panes(self, panes):
        style = wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE|wx.CP_GTK_EXPANDER
        pypanes = []

        for pane_name, ppane in panes:
            pane = PCP.PyCollapsiblePane(self, label=pane_name, style=style)
            pane.Hide()

            font = pane.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            pane._pButton.SetFont(font)

            pane.SetLabel(pane_name)
            pane.SetExpanderDimensions(5, 10)
            self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, pane)
            self.populate_panel(pane, ppane)

            self.panes[pane_name] = pane            
            self.sizer.Add(pane, 0, wx.RIGHT|wx.LEFT|wx.EXPAND, 10)

            ppane.Show()
            pypanes.append(pane)

        return pypanes
            

    def hide_panes(self, panes):
        for pane_name, pane in panes:
            if not pane_name in self.panes:
                continue
                
            pane = self.panes[pane_name]
            pane.Hide()
            success = self.sizer.Detach(pane)
#            success = pane.Reparent(self.doc.app.frame)
            if not success:
                log.warning('reparenting failed in conf_widget')

    def OnPaneChanged(self, event):
        for pane in self.panes.itervalues():
            pane.Refresh()
            
        self.sizer.Layout()
        self.SetupScrolling()

    def get_detail_pane(self, node, type, xpath):
        panes = []
        gens = list(self.doc.get_generators_map().itervalues())

        if type == 'gen':
            data_pane = self.make_gen_details_pane(node, gens, xpath)
            panes.append((node.name + ' Details', data_pane))

        elif type == 'class':
            if issubclass(node, RecipeBasedGenerator):
                _parent, other_parent = node.__bases__
                gen_class = _parent if _parent != RecipeBasedGenerator else \
                                                            other_parent
            else:
                gen_class = node

            name = self.doc.get_generators_map()[gen_class]
            data_pane = self.make_class_details_pane(node, gens, xpath)
            panes.append((name + ' Details', data_pane))

        else:
            data_pane = self.make_geom_details_pane(node)
            panes.append((node.shape + ' Details', data_pane))

        return panes

    def get_property_pane(self, node, type):
        panes = []

        if type == 'gen':
            default_config = node.default_config
            current_config = list(node.config.iteritems())
            name = node.name
        else:
            default_config = node.get_config()
            current_config = None
            name = self.doc.get_generators_map()[node]

        prop_pane = self.make_property_pane(default_config, current_config)
        panes.append((name + ' Attributes', prop_pane))

        return panes

    @logmt
    def on_gen_change(self, name):
        @logfn
        def callback_for_gen_change(node):
            curr_node, type = self.node
            xpath = self.xpath.replace(curr_node.name, name)
            self.update_panes(node, type, xpath)
            self.doc.obtree_widget.select_generator(node)

        self.on_apply(None, callback_for_gen_change)

    def on_sseed(self, sseed):
        self.on_apply(None)

    def on_seed(self, seed):
        self.on_apply(None)

    def make_gen_details_pane(self, node, gens, xpath):
        xpath = xpath
        modified_values = self.get_modified_values()

        name = TextProperty('Name', node.name, node.name)
        _xpath = TextProperty('Xpath', xpath, xpath, is_editable=False)
        visible =  ToggleProperty('Visible', True, True, is_editable=False)
        generate =  ToggleProperty('Generate', True, True)

        sseed_mod = 's_seed' in modified_values
        seed = SeedProperty('Seed', (0, 65535), node.s_seed,
                            is_modified=sseed_mod, on_change=self.on_sseed)
        seed_mod = 'seed' in modified_values
        dseed = SeedProperty('Deep Seed', (0, 65535), node.seed,
                             is_modified=seed_mod, on_change=self.on_seed)

        replace_gen = ChooseProperty('Replace with', gens, '',
                                     on_change=self.on_gen_change,
                                     is_editable=False)

        props = [name, _xpath, visible, generate, seed, dseed, replace_gen]

        pwidget = PropertyWidget(self, props)
        pwidget.Hide()

        return pwidget

    def make_class_details_pane(self, _class, gens, xpath):
        name = self.doc.get_generators_map()[_class]
        modified_values = self.get_modified_values()

        name = TextProperty('Name', name, name)
        _xpath = TextProperty('Xpath', xpath, xpath, is_editable=False)
        visible =  ToggleProperty('Visible', True, True)
        generate =  ToggleProperty('Generate', True, True)

        sseed_mod = 's_seed' in modified_values
        seed = SeedProperty('Seed', (0, 65535), 0, is_modified=sseed_mod)

        seed_mod = 'seed' in modified_values
        dseed = SeedProperty('Deep Seed', (0, 65535), 0, is_modified=seed_mod)

        rgen = self.get_recipe_value('generator')\
                                    if 'generator' in modified_values else ''
        rgen_mod = True if rgen else False
        replace_gen = ChooseProperty('Replace with', gens, rgen,
                                     is_editable=False, is_modified=rgen_mod)

        props = [name, _xpath, visible, generate, seed, dseed, replace_gen]

        pwidget = PropertyWidget(self, props)
        pwidget.Hide()

        return pwidget

    def make_geom_details_pane(self, geom):

        vertices = TextProperty('Vertices', str(geom.num_vertices),
                                                        str(geom.num_vertices),
                                                        is_editable=False)

        triangles = TextProperty('Triangles', str(geom.num_triangles),
                                                        str(geom.num_triangles),
                                                        is_editable=False)

        location =  TextProperty('Location', geom.location, geom.location,
                                                            is_editable=False)

        bbox =  TextProperty('BoundBox', geom.bbox, geom.bbox,
                                                            is_editable=False)

        area = TextProperty('area', str(geom.area), str(geom.area),
                                                            is_editable=False)

        volume = TextProperty('volume', str(geom.volume), str(geom.volume),
                                                            is_editable=False)

        props = [vertices, triangles, location, bbox, area, volume]

        pwidget = PropertyWidget(self, props)
        pwidget.Hide()

        return pwidget

    def get_recipe_value(self, key):
        mod_name = None

        matches = self.doc.recipe.matches
        onmatches = self.doc.recipe.onmatches

        for mname, condition in matches:
            if condition == self.xpath:
                mod_name = mname
                break

        if not mod_name:
            return None

        for onmatch in onmatches:
            omname = onmatch[0]
            if omname == mod_name:
                for _key, value in onmatch[1:]:
                    if key == _key:
                        return value
        return None
    
    def get_modified_values(self):
        modified = {}
        mod_name = None
        matches = self.doc.recipe.data['matches']
        onmatches = self.doc.recipe.data['onmatches']

        for mname, condition in matches:
            if condition == self.xpath:
                mod_name = mname
                break

        if not mod_name:
            return modified

        for onmatch in onmatches:
            omname = onmatch[0]
            if omname == mod_name:
                for key, value in onmatch[1:]:
                    modified[key] = value

        return modified

    def _get_value(self, data, key):
        for k, v in data:
            if k == key:
                return copy.deepcopy(v)

    def make_property_pane(self, default_data, current_data=None):
        modified_values = self.get_modified_values()

        props = []

        # this implementation is so clumsy
        data = current_data or default_data

        for key, value in data:
            modified = 'config.'+key in modified_values

            mod_value = modified_values['config.'+key] if modified else ''
            
            range, value = (self._get_value(default_data, key),
                            mod_value or value) \
                            if current_data else (value, mod_value)
                                                
            prop = self._make_property(key, range, value, modified)
            props.append(prop)

        pwidget = PropertyWidget(self, props)
        pwidget.Hide()

        return pwidget

    def _make_property(self, name, default_value, value, modified):
        if isinstance(default_value, tuple):
            prop = RangeProperty(name, default_value, value,
                                                        is_modified=modified)

        elif isinstance(default_value, list):
            prop = ChooseProperty(name, default_value, value, is_multi=True,
                                                        is_modified=modified)
        
        else:
            prop = TextProperty(name, str(default_value), str(value),
                                                        is_modified=modified)

        return prop

class XpathWidget(wx.HtmlListBox):
    COLORS = [utils.YELLOW, utils.LIGHT_YELLOW]

    def __init__(self, parent):
        wx.HtmlListBox.__init__(self, parent, wx.ID_ANY)

        self.doc = None
        self.xpaths = []
        self.Bind(wx.EVT_LISTBOX, self.on_xpath_sel)

    def OnGetItem(self, n):
        xpath, desc = self.xpaths[n][0], self.xpaths[n][1]

        color = self.COLORS[n % 2]

        html = "<b> <font color='Black'> %s </font> </b>"\
               "<br> <font color='Grey' size='2'>&nbsp %s</font>"\
                    % (desc, xpath)

        html = '<table bgcolor="%s" border="0" '\
               'width="99%%" cellspacing="0px"'\
               'cellpadding="0px"><tr><td>%s</td></tr></table>' % (color, html)

        return html

    @logmt
    def update(self, xpaths, doc):
        self.Freeze()

        self.doc = doc
        self.xpaths = xpaths
        self.SetItemCount(len(xpaths))
        self.SetSelection(0)
        self.Refresh()
        
        self.Thaw()

    @logmt
    def on_xpath_sel(self, event):
        index = event.GetInt()
        xpath, desc, dummy = self.xpaths[index]
        self.doc.select_xpath(xpath, desc)

# ---- Test Code ----
class ConfigFrame(wx.Frame):
    def __init__(self, parent, recipe):
        wx.Frame.__init__(self, parent, title="Configuration", size=(800,600))

        self.config_widget = ConfigurationWidget(self, recipe)
        data = data = [
                ('id', '12'),
                ('seed', 123),
                ('geoms', 'hi'),
                ('sub_gens', 3.43),
                ('location', 'there'),
                ('bbox', 'sdf')
               ]
        config = {
                    'id': ['12','13', '14'],
                    'seed': (3, 40),
                    'geoms': ['hi', 'hello', 'bingo'],
                    'sub_gens': (2.4, 5.4),
                    'location': ['there', 'here'],
                    'bbox': ['sdf', 'asdf']
                        }
#        dp = make_config_pane(self, data, config)
#        dp1 = make_config_pane(self, data, config)
        li = []
        li.append(('Data:', dp))
        li.append(('Data:', dp1))
        self.config_widget.update_panes(li)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.config_widget, 1, wx.EXPAND)
        sizer.Layout()
        self.SetSizer(sizer)

class TestApp(wx.App):
    def __init__(self, recipe):
        wx.App.__init__(self, redirect=False)

        self.frame = ConfigFrame(None, recipe)
        self.frame.Show()

def test():
    from procodile.recipe import RecipeConfig
    rc = RecipeConfig()
    rc.generators.append(['root', '/tmp/', 'bingo.tingo', '0.1'])
    rc.generators.append(['forest', '/tmp/', 'bingo.Forest', '0.3'])
    rc.generators.append(['tree', '/tmp/', 'bingo.Tree', '0.4'])

    rc.matches.append(['alltrees', '//tree'])
    rc.matches.append(['buildings', '//forest/building', '//sector//building'])

    rc.onmatches.append(['alltrees', ['config.width', '10'], ['seed', '10']])
    rc.onmatches.append(['buildings', ['config.num', '54'],
                                ['generator', 'tree']])

    app = TestApp(rc)
    app.MainLoop()

if __name__ == '__main__':
    test()
