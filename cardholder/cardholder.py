import sys
import math
import time 
import os
from itertools import cycle

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QLineEdit


from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QDrag
from PyQt5.QtGui import QMovie

from PyQt5 import QtCore

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QMimeData
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QByteArray

from pkg_resources import resource_string, resource_filename

# =========================
#
# Collect Cards
#
# ========================= 
class CollectCardsThread(QtCore.QThread):
    cards_collected = pyqtSignal(list)
    __instance = None
    __run = False

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance    

    @classmethod
    def get_instance(cls, parent, collect_cards_method, paths=None):
        if not cls.__run:
            inst = cls.__new__(cls)
            cls.__init__(cls.__instance, parent, collect_cards_method, paths) 
            return inst
        else:
            return None

    def __init__(self, parent, collect_cards_method, paths):
        QThread.__init__(self)
        
        self.parent = parent
        self.collect_cards_method = collect_cards_method
        self.paths = paths
        
    def run(self):
        CollectCardsThread.__run = True
        ####
        time.sleep(5)
        ####
        
        card_list = self.collect_cards_method( self.paths)
        self.cards_collected.emit(card_list)
        CollectCardsThread.__run = False

    def __del__(self):
        self.exiting = True
        self.wait()
 
# =========================
#
# Rolling Animation
#
# ========================= 
class AnimateRolling(QThread):
    
    positionChanged = pyqtSignal(int)
    __instance = None
    __run = False
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance    
    
    @classmethod
    def get_instance(cls, loop, value, sleep=0.01):
        if not cls.__run:
            inst = cls.__new__(cls)
            cls.__init__(cls.__instance, loop, value, sleep) 
            return inst
        else:
            return None
    
    def __init__(self, loop, value, sleep):
        QThread.__init__(self)
        self.loop = loop
        self.value = value
        self.sleep = sleep
            
    def __del__(self):
        self.wait()
    
    def run(self): 
        
        # blocks to call again
        AnimateRolling.__run = True
        for i in range(self.loop):
            time.sleep(self.sleep)
            self.positionChanged.emit(self.value)
        
        # release blocking
        AnimateRolling.__run = False


# =========================
#
# CountDown Timer
#
# =========================
class CountDown(QThread):
    
    timeOver = pyqtSignal()
    __timer = 0    
    
    def __init__(self):
        QThread.__init__(self)
            
    def __del__(self):
        self.wait()
    
    def run(self): 

        # Ha meg mukodik
        if CountDown.__timer > 0:
            CountDown.__timer = 10

        # Ha mar nem mukodik
        else:
            CountDown.__timer = 10
        
            while CountDown.__timer > 0:
                time.sleep(0.04)
                CountDown.__timer = CountDown.__timer - 1
                #print(CountDown.__timer)
               
            #print("most emital")
            self.timeOver.emit()


 
# =========================
#
# Card Holder
#
# =========================
class CardHolder( QWidget ):
    
    resized = QtCore.pyqtSignal(int,int)
    moved_to_front = QtCore.pyqtSignal(int)
    
    DEFAULT_SPINNER_NAME = 'spinner.gif'

    DEFAULT_MAX_OVERLAPPED_CARDS = 4    
    DEFAULT_BORDER_WIDTH = 5
    DEFAULT_BACKGROUND_COLOR = QColor(Qt.red)
    DEFAULT_BORDER_RADIUS = 10
    
    CARD_TRESHOLD = 6
    MAX_CARD_ROLLING_RATE = 10
    
    def __init__(self, parent, recent_card_structure, title_hierarchy, get_new_card_method, get_collected_cards_method):
        super().__init__()

        self.get_new_card_method = get_new_card_method
        self.get_collected_cards_method = get_collected_cards_method
        self.parent = parent
        self.title_hierarchy = title_hierarchy
        self.recent_card_structure = recent_card_structure
        
        self.shown_card_list = []
        self.card_descriptor_list = []

        self.set_max_overlapped_cards(CardHolder.DEFAULT_MAX_OVERLAPPED_CARDS, False)        
        self.set_border_width(CardHolder.DEFAULT_BORDER_WIDTH, False)
        self.set_border_radius(CardHolder.DEFAULT_BORDER_RADIUS, False)
        self.set_background_color(CardHolder.DEFAULT_BACKGROUND_COLOR, False)
        
        self.self_layout = QVBoxLayout(self)
        self.setLayout(self.self_layout)

        self.actual_card_index = 0
        self.rate_of_movement = 0
        self.delta_rate = 0
        
        self.countDown = CountDown()
        self.countDown.timeOver.connect(self.animated_move_to_closest_descreet_position)
        
        self.collecting_spinner = None
        spinner_file_name = resource_filename(__name__,os.path.join("img", CardHolder.DEFAULT_SPINNER_NAME))
        self.set_spinner(spinner_file_name)

        # it hides the CardHolder until it is filled up with cards
        self.select_index(0)
        #self.setHidden(True)
        #self.show()

    # ----------------
    #
    # set spinner
    #
    # ----------------
    def set_spinner(self, file_name):

        # remove the old spinner
        if self.collecting_spinner != None:
            self.spinner_movie.stop()            
            self.collecting_spinner.setParent(None)
            self.collecting_spinner = None
            
        self.spinner_movie = QMovie(file_name, QByteArray(), self)
        self.collecting_spinner = QLabel(self.parent)
        self.collecting_spinner.setMovie(self.spinner_movie)
        self.collecting_spinner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.spinner_movie.setCacheMode(QMovie.CacheAll)
        self.spinner_movie.setSpeed(100)
        self.spinner_movie.start()          # if I do not start it, it stays hidden
        self.spinner_movie.stop()
        self.collecting_spinner.move(0,0)
        self.collecting_spinner.show()
        self.collecting_spinner.setHidden(True)

        img_size = self.spinner_movie.currentPixmap().size()
        self.collecting_spinner.resize(img_size.width(), img_size.height())      
        
    # --------------------------------------
    # Shows the spinner + removes all Cards
    # --------------------------------------
    def start_spinner(self):

        # remove all cards
        self.refresh([])

        self.collecting_spinner.move(
            (self.parent.geometry().width()-self.collecting_spinner.width()) / 2,
            (self.parent.geometry().height()-self.collecting_spinner.width()) / 2
        )
        self.spinner_movie.start()
        self.collecting_spinner.setHidden(False)        

    # ------------------------------
    # Hides the spinner
    # ------------------------------
    def stop_spinner(self):
        self.collecting_spinner.setHidden(True)
        self.spinner_movie.stop()

        
    # ---------------------------------------------------------------------
    #
    # start card collection
    #
    # this method should be called when you want a new collection of cards
    #
    # ---------------------------------------------------------------------
    def start_card_collection(self, parameters):

        self.start_spinner()

        self.cc = CollectCardsThread.get_instance( self, self.get_collected_cards_method, parameters )
        if self.cc:
            self.cc.cards_collected.connect(self.refresh)
            self.cc.start()   
        
    # -------------------------------------------------------
    # refres card collection - used by the CollectCardsThread
    # -------------------------------------------------------
    def refresh(self, filtered_card_list): 
        self.stop_spinner()
        self.fill_up_card_descriptor_list(filtered_card_list)
        self.select_actual_card()
        #if self.shown_card_list:
        #    self.setHidden(False)

    # ------------------------------------------------------
    # fill up card descriptor - used by the refresh() method
    # ------------------------------------------------------
    def fill_up_card_descriptor_list(self, filtered_card_list = []):        
        self.card_descriptor_list = []
        for c in filtered_card_list:
            self.card_descriptor_list.append(c)

    def set_border_width(self, width, update=True):
        self.border_width = width
        if update:
            self.update()
        
    def get_border_width(self):
        return self.border_width

    def set_background_color(self, color, update=True):
        self.background_color = color
        ## without this line it wont paint the background, but the children get the background color info
        ## with this line, the rounded corners will be ruined
        #self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        #self.setStyleSheet('background-color: ' + self.background_color.name())
        if update:
            self.update()
        
    def set_max_overlapped_cards(self, number, update=True):
        self.max_overlapped_cards = number
        if update:
            self.select_index(self.actual_card_index)
        
    def set_border_radius(self, radius, update=True):
        self.border_radius = radius
        if update:
            self.update()
        
    def get_max_overlapped_cards(self):
        return self.max_overlapped_cards
  
    def resizeEvent(self, event):
        self.resized.emit(event.size().width(),event.size().height())
        return super(CardHolder, self).resizeEvent(event)
 
    def remove_all_cards(self):
        for card in self.shown_card_list:
            card.setParent(None)
            card = None

    def remove_card(self, card):
        card.setParent(None)
        card = None

    def get_rate_of_movement(self):
        return self.rate_of_movement
    
    def get_delta_rate(self):
        return self.delta_rate

            
        
        





    def select_next_card(self):
        self.select_index(self.actual_card_index + 1)

    def select_previous_card(self):
        self.select_index(self.actual_card_index - 1)
        
    def select_actual_card(self):
        self.select_index(self.actual_card_index)
    
    # --------------------------------------------------------------------------
    #
    # Select Index
    #
    # It builds up from scrach the shown_card_list from the card_descriptor_list
    # In the 0. position will be the Card identified by the "index" parameter
    # The card in the 0. position will be indicated as the "selected"
    #
    # --------------------------------------------------------------------------
    def select_index(self, index):
        index_corr = self.index_correction(index)
        
        self.actual_card_index = index_corr
        self.remove_all_cards()
        position = None
        self.shown_card_list = [None for i in range(index_corr + min(self.max_overlapped_cards, len(self.card_descriptor_list)-1), index_corr - 1, -1) ]
        
        for i in range( index_corr + min(self.max_overlapped_cards, len(self.card_descriptor_list)-1), index_corr - 1, -1):
            i_corr = self.index_correction(i)
            
            if( i_corr < len(self.card_descriptor_list)):

                local_index = i-index_corr
                card = self.get_new_card_method(self.card_descriptor_list[i_corr], local_index, i_corr )                                
                position = card.place(local_index)
                
                self.shown_card_list[local_index] = card

        # if there is at least one Card
        if self.shown_card_list:

            # Control the Height of the CardHolder
            self.setMinimumHeight(position[0].y() + position[1].y() + self.border_width )
            self.setMaximumHeight(position[0].y() + position[1].y() + self.border_width )
        
            # for indicating the selected (0) Card
            self.rolling(0)

        # if ther is NO Card at all
        else:
            # hides the CardHolder
            self.setMinimumHeight(0)
            self.setMaximumHeight(0)

    # for some reason the 2nd parameter is False from connect
    # that is why I cant connect it to directly
    def button_animated_move_to_next(self):
        self.animated_move_to_next()

    def button_animated_move_to_previous(self):
        self.animated_move_to_previous()


    # ---------------------------------
    #
    # Animated shows the next card
    #
    # ---------------------------------
    def animated_move_to_next(self, sleep=0.01):
        rate = self.get_rate_of_movement()
        
        if rate > 0:
            loop = self.MAX_CARD_ROLLING_RATE - rate
        elif rate < 0:
            loop = -rate
        else:
            loop = self.MAX_CARD_ROLLING_RATE
            
        self.animate = AnimateRolling.get_instance(int(loop), 1, sleep)
        if self.animate:
            self.animate.positionChanged.connect(self.rolling)
            self.animate.start()
       
    # ---------------------------------
    #
    # Animated shows the previous card
    #
    # ---------------------------------
    def animated_move_to_previous(self, sleep=0.01):
        rate = self.get_rate_of_movement()
        
        if rate > 0:
            loop = rate
        elif rate < 0:
            loop = self.MAX_CARD_ROLLING_RATE + rate
        else:
            loop = self.MAX_CARD_ROLLING_RATE
            
        self.animate = AnimateRolling.get_instance(int(loop), -1, sleep)
        if self.animate:
            self.animate.positionChanged.connect(self.rolling)
            self.animate.start()
    
    # ------------------------------------------------
    #
    # Animated moves to the closest descreet position
    #
    # ------------------------------------------------
    def animated_move_to_closest_descreet_position(self):
        rate = self.get_rate_of_movement()
        delta_rate = self.get_delta_rate()
        
        if rate != 0:
            
            if rate > 0:
                
                if delta_rate < 0:
                    value = -1
                    loop = rate
                else:
                    value = 1
                    loop = self.MAX_CARD_ROLLING_RATE - rate                    
                
                #if rate >= self.CARD_TRESHOLD:
                #    value = 1
                #    loop = self.MAX_CARD_ROLLING_RATE - rate                    
                #else:
                #    value = -1
                #    loop = rate
        
            elif rate < 0:
                
                if delta_rate < 0:
                    value = -1
                    loop = self.MAX_CARD_ROLLING_RATE + rate
                else:
                    value = 1
                    loop = -rate
                
                #if rate <= -self.CARD_TRESHOLD:
                #    value = -1
                #    loop = self.MAX_CARD_ROLLING_RATE + rate
                #else:
                #    value = 1
                #    loop = -rate
                
            self.animate = AnimateRolling.get_instance(int(loop), value, 0.02)
            if self.animate:
                self.animate.positionChanged.connect(self.rolling)
                self.animate.start()

    # ------------------------------------------------
    #
    # Animated moves to the set position Card
    #
    # ------------------------------------------------
    def animated_move_to(self, position, sleep=0.01):
        self.animate = AnimateRolling.get_instance(position * self.MAX_CARD_ROLLING_RATE, 1, sleep)
        if self.animate:
            self.animate.positionChanged.connect(self.rolling)
            self.animate.start()
        
        
        

    # ---------------------------------------------------------------------
    #
    # Rolling Wheel
    #
    # Rolls the cards according to the self.rate_of_movement + delta_rate
    # Plus it starts a Timer. If the timer expires, the cards will be 
    # moved to the first next discreet position
    #
    # --------------------------------------------------------------------
    def rolling_wheel(self, delta_rate):
        self.rolling(delta_rate)
        
        if self.rate_of_movement != 0:
            self.countDown.start()

    # --------------------------------------------------------------------
    #
    # ROLLING
    #
    # Rolls the cards according to the self.rate_of_movement + delta_rate
    #
    # delta_rate:   In normal case it is +1 or -1
    #               Adding this value to the self.rate_of_movement, it
    #               shows that how far the cards moved negativ (up) or
    #               positive (down) direction compared to the default
    #               (local_index) value
    #               -10 means (-100%) it moved to the next position, 
    #               +10 means (+100%) it moved to the previous position
    #
    # -------------------------------------------------------------------
    def rolling(self, delta_rate):
        
        self.delta_rate = delta_rate
        
        if self.rate_of_movement >= self.MAX_CARD_ROLLING_RATE or self.rate_of_movement <= -self.MAX_CARD_ROLLING_RATE:
            self.rate_of_movement = 0

        self.rate_of_movement = self.rate_of_movement + delta_rate

        # Did not start to roll
        if len(self.shown_card_list) <= self.get_max_overlapped_cards() + 1:
            
            # indicates that the first card is not the selected anymore
            card = self.shown_card_list[0]
            card.set_not_selected()
            
            # add new card to the beginning
            first_card = self.shown_card_list[0]                
            first_card_index = self.index_correction(first_card.index - 1)
            card = self.get_new_card_method(self.card_descriptor_list[first_card_index], -1, first_card_index ) 
            self.shown_card_list.insert(0, card)
            
            # add a new card to the end
            last_card = self.shown_card_list[len(self.shown_card_list)-1]                
            last_card_index = self.index_correction(last_card.index + 1)
            card = self.get_new_card_method(self.card_descriptor_list[last_card_index], self.get_max_overlapped_cards() + 1, last_card_index ) 
            self.shown_card_list.append(card)
            
            # Re-print to avoid the wrong-overlapping
            for card in self.shown_card_list[::-1]:
                card.setParent(None)
                card.setParent(self)
                card.show()        

        # adjust
        rate = self.rate_of_movement / self.MAX_CARD_ROLLING_RATE
        if self.rate_of_movement >= 0:
            self.rolling_adjust_forward(rate)
        else:
            self.rolling_adjust_backward(rate)

        # indicates that the first card is the selected            
        if self.rate_of_movement == 0:
            card = self.shown_card_list[0]
            card.set_selected()

        # show the cards in the right position
        rate = self.rate_of_movement / self.MAX_CARD_ROLLING_RATE
        for i, card in enumerate(self.shown_card_list):
            virtual_index = card.local_index - rate
            card.place(virtual_index, True)


#print( [(c.local_index, c.card_data) for c in self.shown_card_list])

    def rolling_adjust_forward(self,rate):
        
        if rate >= 1.0:
            self.rate_of_movement = 0
            
            # remove the first 2 cards from the list and from CardHolder
            for i in range(2):
                card_to_remove = self.shown_card_list.pop(0)
                card_to_remove.setParent(None)

            # re-index
            for i, card in enumerate(self.shown_card_list):
                card.local_index = i
                
        elif rate == 0:
            # remove the first card from the list and from CardHolder
            card_to_remove = self.shown_card_list.pop(0)
            card_to_remove.setParent(None)
            
            # remove the last card from the list and from CardHolder
            card_to_remove = self.shown_card_list.pop(len(self.shown_card_list) - 1)
            card_to_remove.setParent(None)
            
            

    def rolling_adjust_backward(self,rate):
        
        if rate <= -1.0:
            self.rate_of_movement = 0
        
            # remove the 2 last cards from the list and from CardHolder
            for i in range(2):
                card_to_remove = self.shown_card_list.pop(len(self.shown_card_list) - 1)
                card_to_remove.setParent(None)
            
            # re-index
            for i, card in enumerate(self.shown_card_list):
                card.local_index = i

    # -----------------------------------------------------------
    #
    # INDEX CORRECTION
    #
    # if the index > numbers of the cards then it gives back 0
    #    as the next index
    # if the index < 0 then it gives back the index of the last
    #    card as the previous index
    #
    # that is how it actually accomplishes an endless loop
    #
    # -----------------------------------------------------------
    def index_correction(self, index):
        if self.card_descriptor_list:
            return (len(self.card_descriptor_list) - abs(index) if index < 0 else index) % len(self.card_descriptor_list)
        else:
            return index


















        
#    def enterEvent(self, event):
#        self.rate_of_movement = 0

    # Mouse Hover out
#    def leaveEvent(self, event):
#        self.rate_of_movement = 0


    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setBrush( self.background_color )

        qp.drawRoundedRect(0, 0, s.width(), s.height(), self.border_radius, self.border_radius)
        qp.end()  

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        value = event.angleDelta().y()/8/15   # in normal case it is +1 or -1
        self.rolling_wheel(value)
  
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            self.animated_move_to_next(sleep=0.03)
        elif event.key() == QtCore.Qt.Key_Down:
            self.animated_move_to_previous(sleep=0.03)
        event.accept()
  
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            #order = sum([i if c.underMouse() else 0 for i, c in enumerate(self.shown_card_list)])
            #self.animated_move_to( order )
            
            self.drag_start_position = event.pos()
            self.card_start_position = self.geometry().topLeft()


    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        delta_y = self.get_delta_y(event.pos().y())  
        self.drag_start_position = event.pos()
        
        self.rolling_wheel(delta_y)
        #print(delta_y)
        #self.drag_card(delta_y)        
        
#        #self.move( tl.x(), tl.y() +  (event.pos().y() - self.drag_start_position.y()) )

#    def mouseReleaseEvent(self, event):
#        self.parent.drop_card(self.local_index, self.index)
#        self.drag_start_position = None
#        self.card_start_position = None
        
        return QWidget.mouseMoveEvent(self, event)

    def get_delta_y(self, y):
        tl=self.geometry().topLeft()
        return tl.y() +  (y - self.drag_start_position.y()) - self.card_start_position.y()



        
  
  
  
  
  
# ==========================================================
#
# Panel
#
# This Panel is inside the Card and contains all widget
# what the user what to show on a Card.
# This Panel has rounded corner which is calculated by the
# radius of the Card and the widht of the border.
#
# ==========================================================
class Panel(QWidget):
    DEFAULT_BORDER_WIDTH = 5
    DEFAULT_BACKGROUND_COLOR = QColor(Qt.lightGray)
    
    def __init__(self):
        super().__init__()
        
        self.self_layout = QVBoxLayout()
        self.self_layout.setSpacing(1)
        self.setLayout(self.self_layout)

        self.set_background_color(Panel.DEFAULT_BACKGROUND_COLOR, False)        
        self.set_border_width(Panel.DEFAULT_BORDER_WIDTH, False)
        #self.set_border_radius(border_radius, False)

    def get_layout(self):
        return self.self_layout
    
    def set_border_radius(self, radius, update=True):
        self.border_radius = radius
        if update:
            self.update()
        
    def set_border_width(self, width, update=True):
        self.border_width = width
        self.self_layout.setContentsMargins( self.border_width, self.border_width, self.border_width, self.border_width )
        if update:
            self.update()

    def set_background_color(self, color, update=True):
        self.background_color = color
        
        ## without this line it wont paint the background, but the children get the background color info
        ## with this line, the rounded corners will be ruined
        #self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet('background-color: ' + self.background_color.name())
        
        if update:            
            self.update()
    
    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setBrush( self.background_color )

        qp.drawRoundedRect(0, 0, s.width(), s.height(), self.border_radius, self.border_radius)
        qp.end()    
    

# ==================
#
# Card
#
# ==================
class Card(QWidget):

    STATUS_NORMAL = 0
    STATUS_SELECTED = 1
    DTATUS_DISABLED = 2
    
    DEFAULT_RATE_OF_WIDTH_DECLINE = 10
    DEFAULT_BORDER_WIDTH = 2
    DEFAULT_BORDER_RADIUS = 10
    
    DEFAULT_BORDER_NORMAL_COLOR = QColor(Qt.green)
    DEFAULT_BORDER_SELECTED_COLOR = QColor(Qt.red)
    DEFAULT_BORDER_DISABLED_COLOR = QColor(Qt.lightGray)
    
    DEFAULT_STATUS = STATUS_NORMAL
    
    
    def __init__(self, card_data, card_holder, local_index, index):
        super().__init__(card_holder)

        self.card_data = card_data
        self.index = index
        self.local_index = local_index
        self.card_holder = card_holder
        self.actual_position = 0
        
        self.self_layout = QVBoxLayout(self)
        self.setLayout(self.self_layout)
        #self.self_layout.setContentsMargins(self.border_width,self.border_width,self.border_width,self.border_width)
        self.self_layout.setSpacing(0)
        
        self.set_border_normal_color(Card.DEFAULT_BORDER_NORMAL_COLOR)
        self.set_border_selected_color(Card.DEFAULT_BORDER_SELECTED_COLOR)
        self.set_border_disabled_color(Card.DEFAULT_BORDER_DISABLED_COLOR)
        
        ## without this line it wont paint the background, but the children get the background color info
        ## with this line, the rounded corners will be ruined
        #self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        #self.setStyleSheet('background-color: ' + "yellow")  

        # Panel where the content could be placed
        self.panel = Panel()
        self.panel_layout = self.panel.get_layout()
        self.self_layout.addWidget(self.panel)
        
        self.border_radius = Card.DEFAULT_BORDER_RADIUS
        self.set_border_width(Card.DEFAULT_BORDER_WIDTH, False)
        self.set_border_radius(Card.DEFAULT_BORDER_RADIUS, False)        
        self.set_rate_of_width_decline(Card.DEFAULT_RATE_OF_WIDTH_DECLINE, False)
        
        self.set_status(Card.STATUS_NORMAL)
        
        # Connect the widget to the Container's Resize-Event
        self.card_holder.resized.connect(self.resized)
        
        self.drag_start_position = None
        #self.setDragEnabled(True)
        #self.setAcceptDrops(True)
 
    def set_selected(self):
        self.set_status(Card.STATUS_SELECTED, True)
        
    def set_not_selected(self):
        self.set_status(Card.STATUS_NORMAL, True)
        
    def set_status(self, status, update=False):
        self.status = status

        if status == Card.STATUS_NORMAL:        
            self.set_border_color(self.get_border_normal_color(), update)
        elif status == Card.STATUS_SELECTED:
            self.set_border_color(self.get_border_selected_color(), update)
        elif status == Card.STATUS_DISABLED:
            self.set_border_color(self.get_border_disabled_color(), update)

    def refresh_color(self):
        self.update()

    def set_border_color(self, color, update):
        self.border_color = color
        if update:
            self.update()

    def get_border_normal_color(self):
        return self.border_normal_color
    
    def get_border_selected_color(self):
        return self.border_selected_color
    
    def get_border_disabled_color(self):
        return self.border_disabled_color
    
    def set_border_normal_color(self, color):
        self.border_normal_color = color
        
    def set_border_selected_color(self, color):
        self.border_selected_color = color
        
    def set_border_disabled_color(self, color):
        self.border_disabled_color = color
        
        
        
 
    def set_background_color(self, color):
        #self.background_color = color
        #self.setStyleSheet('background-color: ' + self.background_color.name())
        #self.update()
        self.panel.set_background_color(color)

    def set_border_width(self, width, update=True):
        self.border_width = width
        self.self_layout.setContentsMargins(self.border_width,self.border_width,self.border_width,self.border_width)
        self.panel.set_border_radius(self.border_radius - self.border_width, update)
        if update:
            self.update()

    def set_border_radius(self, radius, update=True):
        self.border_radius = radius
        self.panel.set_border_radius(self.border_radius - self.border_width, update)
        if update:
            self.update()

    def set_rate_of_width_decline(self, rate, update=True):
        self.rate_of_width_decline = rate
    
    
    def get_panel(self):
        return self.panel
 
    def paintEvent(self, event):
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setBrush(self.border_color)

        qp.drawRoundedRect(0, 0, s.width(), s.height(), self.border_radius, self.border_radius)
        qp.end()
 
 
 
 
 
#    def mousePressEvent(self, event):
#        if event.button() == Qt.LeftButton:
#            self.drag_start_position = event.pos()
#            self.card_start_position = self.geometry().topLeft()
#
#    def mouseMoveEvent(self, event):
#        if not (event.buttons() & Qt.LeftButton):
#            return
#        delta_y = self.get_delta_y(event.pos().y())        
#        self.parent.drag_card(self.local_index, self.index, delta_y)        
#        
#        #self.move( tl.x(), tl.y() +  (event.pos().y() - self.drag_start_position.y()) )
#
#    def mouseReleaseEvent(self, event):
#        #delta_y = self.get_delta_y(event.pos().y())
#        self.parent.drop_card(self.local_index, self.index)
#        self.drag_start_position = None
#        self.card_start_position = None
#        
#
#    def get_delta_y(self, y):
#        tl=self.geometry().topLeft()
#        return tl.y() +  (y - self.drag_start_position.y()) - self.card_start_position.y()














        
 
#    def mouseMoveEvent(self, event):
#        if not (event.buttons() & Qt.LeftButton):
#            return
#        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
#            return
#        drag = QDrag(self)
#        mimedata = QMimeData()
#        
#        #mimedata.setText(self.text())
#        mimedata.setText(str(self.index))
#        
#        drag.setMimeData(mimedata)
#        pixmap = QPixmap(self.size())
#        painter = QPainter(pixmap)
##        painter.drawPixmap(self.rect(), self.grab())
#        painter.end()
#        drag.setPixmap(pixmap)
#        drag.setHotSpot(event.pos())
#        drag.exec_(Qt.CopyAction | Qt.MoveAction)

 
#    def mousePressEvent(self, event):
#        if event.button() == Qt.LeftButton:
#            self.drag_start_position = event.pos()
#        #self.parent.resized.connect(self.resized)
#        #self.parent.moved_to_front.emit(self.index)
#        
#        if self.local_index != 0:
#            self.parent.select_index(self.index)
        
#    def dragEnterEvent(self, e):
           
   
    # ---------------------------------------------
    # The offset of the Card from the left side as 
    # 'The farther the card is the narrower it is'
    # ---------------------------------------------
    def get_x_offset(self, local_index):
        return  local_index * self.rate_of_width_decline
 
    # ----------------------------------------
    #
    # Resize the width of the Card
    #
    # It is called when:
    # 1. CardHolder emits a resize event
    # 2. The Card is created and Placed
    #
    # ----------------------------------------
    def resized(self, width, height, local_index=None):
        # The farther the card is the narrower it is
        if local_index==None:
            local_index = self.local_index
        standard_width = width - 2*self.card_holder.get_border_width() - 2*self.get_x_offset(local_index)
        self.resize( standard_width, self.sizeHint().height() )

    # ---------------------------------------
    #
    # Place the Card into the given position
    #
    # 0. position means the card is in front
    # 1. position is behind the 0. position
    # and so on
    # ---------------------------------------
    def place(self, local_index, front_remove=False):
        
        # Need to resize and reposition the Car as 'The farther the card is the narrower it is'
        self.resized(self.card_holder.width(), self.card_holder.height(), local_index)
        x_position = self.card_holder.get_border_width() + self.get_x_offset(local_index)
        y_position = self.card_holder.get_border_width() + self.get_y_position(local_index)
        
        if front_remove:
            y_position = y_position - local_index * (math.exp(5 - 5 * local_index) / 2000) * self.height()
            
        self.move( x_position, y_position )
        
        self.show()
        
        return(QPoint(x_position, y_position), QPoint(self.width(),self.height()))

    def get_y_position(self, local_index):
        max_card = self.card_holder.get_max_overlapped_cards()
        return ( max_card - min(local_index, max_card) ) * ( self.card_holder.get_max_overlapped_cards() - local_index ) * 6
