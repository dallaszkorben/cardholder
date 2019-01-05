import sys
import os

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QApplication

from PyQt5.QtGui import QColor

from PyQt5.QtCore import Qt

from pkg_resources import resource_string, resource_filename

IMG_SPINNER = 'spinner.gif'

from cardholder.cardholder import CardHolder
from cardholder.cardholder import Card

class App(QWidget):
 
    def __init__(self):
        super().__init__()
        self.title = 'Card selector'
        self.left = 10
        self.top = 10
        self.width = 420
        self.height = 300
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height) 
        self.setStyleSheet('background: gray')
 
        self.scroll_layout = QVBoxLayout(self)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.setSpacing(0)
        self.setLayout(self.scroll_layout)
        
        spinner_file_name = resource_filename(__name__,os.path.join("cardholder", "img", IMG_SPINNER))
        print(spinner_file_name)

        self.actual_card_holder = CardHolder(            
            self, 
            [],
            spinner_file_name,
            "Kezdocim",            
            self.get_new_card,
            self.collect_cards
        )
        
        self.actual_card_holder.set_background_color(QColor(Qt.yellow))
        self.actual_card_holder.set_border_width(10)
        self.scroll_layout.addWidget(self.actual_card_holder)
        
        next_button = QPushButton("next",self)
        next_button.clicked.connect(self.actual_card_holder.button_animated_move_to_next)
        next_button.setFocusPolicy(Qt.NoFocus)
        
        previous_button = QPushButton("prev",self)
        previous_button.clicked.connect(self.actual_card_holder.button_animated_move_to_previous)
        previous_button.setFocusPolicy(Qt.NoFocus)

        fill_up_button = QPushButton("fill up",self)
        fill_up_button.clicked.connect(self.fill_up)
        fill_up_button.setFocusPolicy(Qt.NoFocus)

        self.scroll_layout.addStretch(1)
        self.scroll_layout.addWidget(previous_button)
        self.scroll_layout.addWidget(next_button)
        self.scroll_layout.addWidget(fill_up_button)
        
        self.actual_card_holder.setFocus()

        self.show()
        
    def fill_up(self):
        self.actual_card_holder.start_card_collection([])
        
    def collect_cards(self, paths):   
        cdl = []        
        cdl.append("Elso")
        cdl.append("Masodik")
        cdl.append("Harmadik")
        cdl.append("Negyedik")
        cdl.append("Otodik")
        cdl.append("Hatodik")
        cdl.append("Hetedik")
        cdl.append("Nyolcadik")
        cdl.append("Kilencedik")
        cdl.append("Tizedik")        
        return cdl
        
    def get_new_card(self, card_data, local_index, index):
        card = Card(card_data, self.actual_card_holder, local_index, index)
        
        card.set_border_selected_color(QColor(Qt.blue))
        #card.set_background_color(QColor(Qt.white))
        #card.set_border_radius( 15 )
        #card.set_border_width(8)
        
        panel = card.get_panel()
        layout = panel.get_layout()
        
        # Construct the Card
        label=QLabel(card_data + "\n\n\n\n\n\n\n\n\n\nHello")
        layout.addWidget(label)
        #layout.addWidget(QPushButton("hello"))
        
        return card
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    #ex.start_card_holder()
    sys.exit(app.exec_())
