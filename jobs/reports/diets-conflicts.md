# Eating links on which places disagree (456 pairs)

Written by `python3 build/diets.py pack --legacy --report <file>`. The table takes the most common value; a place that differs keeps its own entry (an override).

- same evidence, different kind (eaten as food or scavenged): 58
- different evidence: 398 (of which the level differs: 398)

| prey | eaten by | places | evidence (count) | kind (count) |
|---|---|---|---|---|
| Odocoileus virginianus | Procyon lotor | 218 | g x204; ga x14 | e x217, s x1 |
| Odocoileus virginianus | Cathartes aura | 137 | g x137 | s x135, e x2 |
| Odocoileus virginianus | Canis latrans | 130 | g x130 | e x127, s x3 |
| Sciurus carolinensis | Procyon lotor | 118 | g x116; ga x2 | e x118 |
| Sylvilagus floridanus | Procyon lotor | 97 | g x95; ga x2 | e x97 |
| Procyon lotor | Canis latrans | 72 | g x70; ga x2 | e x72 |
| Sciurus carolinensis | Cathartes aura | 67 | g x63; ga x4 | s x63, e x4 |
| Sylvilagus floridanus | Cathartes aura | 62 | g x61; ga x1 | s x60, e x2 |
| Odocoileus virginianus | Vulpes vulpes | 61 | g x53; ga x8 | e x59, s x2 |
| Odocoileus hemionus | Canis latrans | 57 | g x55; ga x2 | e x50, s x7 |
| Odocoileus virginianus | Didelphis virginiana | 57 | g x55; ga x2 | e x55, s x2 |
| Castor canadensis | Ursus americanus | 52 | g x49; ga x3 | e x52 |
| Fagus grandifolia | Castor canadensis | 50 | g x49; ga x1 | e x50 |
| Callicarpa americana | Sciurus carolinensis | 48 | g x47; ga x1 | e x48 |
| Juniperus virginiana | Odocoileus virginianus | 48 | gf x46; ga x1; g x1 | e x48 |
| Castor canadensis | Canis latrans | 45 | g x42; ga x3 | e x45 |
| Corvus corax | Canis latrans | 44 | g x31; ga x13 | e x44 |
| Liquidambar styraciflua | Corvus brachyrhynchos | 44 | g x43; ga x1 | e x44 |
| Corvus brachyrhynchos | Canis latrans | 40 | g x39; ga x1 | e x40 |
| Odocoileus hemionus | Ursus americanus | 39 | g x37; ga x2 | e x33, s x6 |
| Pituophis catenifer | Canis latrans | 35 | g x34; ga x1 | e x35 |
| Odocoileus hemionus | Buteo jamaicensis | 34 | g x19; ga x15 | e x34 |
| Corvus corax | Canis lupus | 31 | ga x30; g x1 | e x31 |
| Odocoileus virginianus | Haliaeetus leucocephalus | 30 | g x30 | e x25, s x5 |
| Castor canadensis | Cathartes aura | 28 | g x27; ga x1 | s x27, e x1 |
| Fagus grandifolia | Sciurus carolinensis | 28 | gf x25; a x3 | e x28 |
| Tamias striatus | Cathartes aura | 28 | g x26; ga x2 | s x26, e x2 |
| Vulpes vulpes | Canis lupus | 28 | ga x21; g x7 | e x28 |
| Odocoileus virginianus | Urocyon cinereoargenteus | 26 | g x23; ga x3 | e x26 |
| Tsuga canadensis | Castor canadensis | 25 | g x24; ga x1 | e x25 |
| Castor canadensis | Vulpes vulpes | 24 | g x19; ga x5 | e x24 |
| Fagus grandifolia | Procyon lotor | 24 | gf x23; a x1 | e x24 |
| Parthenocissus quinquefolia | Odocoileus virginianus | 24 | g x23; ga x1 | e x24 |
| Procyon lotor | Lynx rufus | 24 | g x21; ga x3 | e x24 |
| Alces alces | Ursus americanus | 23 | g x22; ga x1 | e x23 |
| Corvus brachyrhynchos | Haliaeetus leucocephalus | 23 | g x22; ga x1 | e x23 |
| Corvus corax | Buteo jamaicensis | 23 | g x21; ga x2 | e x23 |
| Peromyscus maniculatus | Cathartes aura | 23 | g x17; ga x6 | s x12, e x11 |
| Pinus strobus | Procyon lotor | 23 | g x22; ga x1 | e x23 |
| Juniperus virginiana | Turdus migratorius | 22 | g x21; ga x1 | e x22 |
| Antilocapra americana | Canis latrans | 20 | g x20 | e x19, s x1 |
| Fagus grandifolia | Vulpes vulpes | 20 | g x17; ga x3 | e x20 |
| Odocoileus virginianus | Buteo jamaicensis | 20 | g x15; ga x5 | e x20 |
| Urocyon cinereoargenteus | Canis latrans | 20 | g x16; ga x4 | e x20 |
| Vulpes vulpes | Canis latrans | 20 | g x17; ga x3 | e x20 |
| Alces alces | Corvus corax | 19 | g x17; ga x2 | s x16, e x3 |
| Branta canadensis | Haliaeetus leucocephalus | 19 | g x18; ga x1 | e x19 |
| Procyon lotor | Haliaeetus leucocephalus | 18 | g x17; ga x1 | e x18 |
| Alces alces | Ursus arctos | 17 | g x17 | e x14, s x3 |
| Castor canadensis | Haliaeetus leucocephalus | 17 | g x14; ga x3 | e x17 |
| Odocoileus virginianus | Pandion haliaetus | 17 | g x16; ga x1 | e x17 |
| Capreolus capreolus | Vulpes vulpes | 16 | g x12; ga x4 | e x12, s x4 |
| Castor canadensis | Lynx rufus | 16 | g x15; ga x1 | e x16 |
| Alces alces | Vulpes vulpes | 15 | g x11; ga x4 | e x9, s x6 |
| Loxodonta africana | Crocuta crocuta | 15 | g x7; ga x8 | e x11, s x4 |
| Loxodonta africana | Panthera leo | 15 | g x8; ga x7 | e x15 |
| Sylvilagus floridanus | Haliaeetus leucocephalus | 15 | g x14; ga x1 | e x15 |
| Tamiasciurus hudsonicus | Cathartes aura | 15 | g x14; ga x1 | s x14, e x1 |
| Tamiasciurus hudsonicus | Haliaeetus leucocephalus | 15 | g x12; ga x3 | e x15 |
| Asclepias speciosa | Anas platyrhynchos | 14 | gg x8; gf x6 | e x14 |
| Cathartes aura | Haliaeetus leucocephalus | 14 | g x13; ga x1 | e x14 |
| Pinus ponderosa | Odocoileus hemionus | 14 | gf x12; a x2 | e x14 |
| Branta canadensis | Buteo jamaicensis | 13 | g x12; ga x1 | e x13 |
| Capreolus capreolus | Corvus corax | 13 | ga x2; g x11 | e x2, s x11 |
| Sus scrofa | Procyon lotor | 13 | g x12; ga x1 | e x13 |
| Taxidea taxus | Canis latrans | 13 | g x12; ga x1 | e x13 |
| Vulpes vulpes | Ursus arctos | 13 | ga x11; g x2 | e x13 |
| Capreolus capreolus | Ursus arctos | 12 | g x6; ga x6 | e x11, s x1 |
| Corvus corax | Aquila chrysaetos | 12 | ga x11; g x1 | e x12 |
| Pituophis catenifer | Lynx rufus | 12 | g x10; ga x2 | e x12 |
| Sciurus carolinensis | Pandion haliaetus | 12 | g x11; ga x1 | e x12 |
| Abies balsamea | Odocoileus virginianus | 11 | g x10; ga x1 | e x11 |
| Asclepias syriaca | Anas platyrhynchos | 11 | g x9; gf x2 | e x11 |
| Corvus corax | Haliaeetus leucocephalus | 11 | g x8; ga x3 | e x11 |
| Hippopotamus amphibius | Crocodylus niloticus | 11 | g x7; ga x4 | e x9, s x2 |
| Phytolacca americana | Vulpes vulpes | 11 | g x10; ga x1 | e x11 |
| Sus scrofa | Ursus arctos | 11 | g x6; ga x5 | e x11 |
| Alces alces | Canis latrans | 10 | g x8; ga x2 | s x3, e x7 |
| Capreolus capreolus | Buteo buteo | 10 | ga x7; g x3 | e x7, s x3 |
| Castor canadensis | Corvus corax | 10 | ga x9; g x1 | e x10 |
| Cervus canadensis | Canis latrans | 10 | g x10 | e x6, s x4 |
| Cervus elaphus | Vulpes vulpes | 10 | g x7; ga x3 | e x5, s x5 |
| Ericameria nauseosa | Odocoileus hemionus | 10 | gf x9; a x1 | e x10 |
| Fagus grandifolia | Lepus americanus | 10 | g x9; ga x1 | e x10 |
| Hippopotamus amphibius | Panthera leo | 10 | g x6; ga x4 | e x10 |
| Otospermophilus variegatus | Canis latrans | 10 | g x9; ga x1 | e x10 |
| Otospermophilus variegatus | Cathartes aura | 10 | g x8; ga x2 | s x7, e x3 |
| Ovis canadensis | Canis latrans | 10 | g x6; ga x4 | e x10 |
| Sciurus carolinensis | Haliaeetus leucocephalus | 10 | g x9; ga x1 | e x10 |
| Sus scrofa | Felis catus | 10 | g x7; ga x3 | e x10 |
| Syncerus caffer | Crocuta crocuta | 10 | g x9; ga x1 | e x9, s x1 |
| Tamiasciurus hudsonicus | Corvus corax | 10 | ga x9; g x1 | e x10 |
| Vaccinium myrtillus | Vulpes vulpes | 10 | ga x8; g x2 | e x10 |
| Zenaida asiatica | Canis latrans | 10 | g x8; ga x2 | e x10 |
| Abies balsamea | Castor canadensis | 9 | ga x2; g x7 | e x9 |
| Canis latrans | Puma concolor | 9 | ga x7; g x2 | e x9 |
| Cervus canadensis | Corvus corax | 9 | g x9 | s x8, e x1 |
| Cervus elaphus | Ursus americanus | 9 | g x9 | e x8, s x1 |
| Elephas maximus | Panthera tigris | 9 | ga x3; g x6 | e x9 |
| Hippopotamus amphibius | Crocuta crocuta | 9 | g x3; ga x6 | e x8, s x1 |
| Lepus americanus | Canis lupus | 9 | g x7; ga x2 | e x9 |
| Mitchella repens | Vulpes vulpes | 9 | g x8; ga x1 | e x9 |
| Mustela erminea | Canis lupus | 9 | g x2; ga x7 | e x9 |
| Odocoileus hemionus | Aquila chrysaetos | 9 | ga x7; g x2 | e x9 |
| Odocoileus hemionus | Haliaeetus leucocephalus | 9 | g x7; ga x2 | e x9 |
| Odocoileus hemionus | Urocyon cinereoargenteus | 9 | g x6; ga x3 | e x8, s x1 |
| Odocoileus hemionus | Vulpes vulpes | 9 | g x9 | e x8, s x1 |
| Otospermophilus variegatus | Puma concolor | 9 | g x5; ga x4 | e x9 |
| Sciurus niger | Haliaeetus leucocephalus | 9 | g x8; ga x1 | e x9 |
| Sus scrofa | Lynx lynx | 9 | ga x7; g x2 | e x9 |
| Capra sibirica | Canis lupus | 8 | g x7; ga x1 | e x7, s x1 |
| Cervus elaphus | Canis latrans | 8 | g x7; ga x1 | e x7, s x1 |
| Juniperus osteosperma | Odocoileus hemionus | 8 | gf x4; a x4 | e x8 |
| Larrea tridentata | Zenaida asiatica | 8 | g x7; ga x1 | e x8 |
| Leopardus pardalis | Panthera onca | 8 | g x3; ga x5 | e x8 |
| Lepus californicus | Cathartes aura | 8 | g x8 | s x7, e x1 |
| Odocoileus virginianus | Pekania pennanti | 8 | g x8 | e x5, s x3 |
| Opuntia polyacantha | Antilocapra americana | 8 | gf x7; a x1 | e x8 |
| Pan troglodytes | Panthera pardus | 8 | g x6; ga x2 | e x8 |
| Panthera leo | Crocuta crocuta | 8 | gg x8 | s x7, e x1 |
| Populus tremuloides | Ursus americanus | 8 | g x7; ga x1 | e x8 |
| Rangifer tarandus | Ursus arctos | 8 | g x8 | e x7, s x1 |
| Rupicapra rupicapra | Aquila chrysaetos | 8 | ga x2; g x6 | e x6, s x2 |
| Rupicapra rupicapra | Ursus arctos | 8 | g x7; ga x1 | e x4, s x4 |
| Rupicapra rupicapra | Vulpes vulpes | 8 | g x3; ga x5 | s x3, e x5 |
| Sus scrofa | Canis aureus | 8 | g x6; ga x2 | e x4, s x4 |
| Sylvilagus audubonii | Cathartes aura | 8 | g x8 | s x7, e x1 |
| Tamiasciurus hudsonicus | Canis lupus | 8 | g x4; ga x4 | e x8 |
| Ursus americanus | Puma concolor | 8 | ga x7; g x1 | e x8 |
| Vaccinium uliginosum | Corvus corax | 8 | g x7; ga x1 | e x8 |
| Zenaida asiatica | Cathartes aura | 8 | g x6; ga x2 | s x6, e x2 |
| Zenaida asiatica | Crotalus atrox | 8 | g x7; ga x1 | e x8 |
| Alces alces | Haliaeetus leucocephalus | 7 | g x3; ga x4 | e x6, s x1 |
| Cervus elaphus | Aquila chrysaetos | 7 | ga x4; g x3 | e x5, s x2 |
| Datura wrightii | Corvus corax | 7 | gf x3; gg x4 | e x7 |
| Fagus sylvatica | Corvus corax | 7 | ga x6; g x1 | e x7 |
| Halimeda | Chelonia mydas | 7 | ga x2; g x5 | e x7 |
| Kobus kob | Crocuta crocuta | 7 | g x7 | e x5, s x2 |
| Loxodonta africana | Crocodylus niloticus | 7 | g x1; ga x6 | e x7 |
| Loxodonta africana | Gyps africanus | 7 | g x6; ga x1 | e x3, s x4 |
| Lynx canadensis | Canis lupus | 7 | ga x5; g x2 | e x7 |
| Microtus pennsylvanicus | Ursus americanus | 7 | g x5; ga x2 | e x7 |
| Odocoileus virginianus | Taxidea taxus | 7 | g x7 | e x6, s x1 |
| Pecari tajacu | Urocyon cinereoargenteus | 7 | g x4; ga x3 | e x7 |
| Populus tremuloides | Odocoileus hemionus | 7 | gf x5; a x2 | e x7 |
| Prunus serotina | Vulpes vulpes | 7 | g x6; ga x1 | e x7 |
| Prunus virginiana | Odocoileus hemionus | 7 | gf x6; a x1 | e x7 |
| Salix | Ursus arctos | 7 | g x1; ga x6 | e x7 |
| Sciurus vulgaris | Canis lupus | 7 | ga x5; g x2 | e x7 |
| Sus scrofa | Panthera pardus | 7 | g x6; ga x1 | e x7 |
| Syncerus caffer | Crocodylus niloticus | 7 | g x2; ga x5 | e x7 |
| Syncerus caffer | Lycaon pictus | 7 | g x2; ga x5 | e x7 |
| Syncerus caffer | Panthera pardus | 7 | g x2; ga x5 | e x7 |
| Vaccinium myrtillus | Cervus elaphus | 7 | g x5; ga x2 | e x7 |
| Abies balsamea | Canis latrans | 6 | ga x4; g x2 | e x6 |
| Ateles geoffroyi | Panthera onca | 6 | g x3; ga x3 | e x6 |
| Canis aureus | Canis lupus | 6 | ga x3; g x3 | e x6 |
| Cervus canadensis | Cathartes aura | 6 | ga x2; g x4 | e x2, s x4 |
| Cervus canadensis | Ursus americanus | 6 | g x6 | e x5, s x1 |
| Cynomys ludovicianus | Cathartes aura | 6 | g x5; ga x1 | e x2, s x4 |
| Didelphis virginiana | Haliaeetus leucocephalus | 6 | g x5; ga x1 | e x6 |
| Equus quagga | Lycaon pictus | 6 | g x5; ga x1 | e x6 |
| Erethizon dorsatus | Vulpes vulpes | 6 | g x4; ga x2 | e x6 |
| Fagus sylvatica | Ursus arctos | 6 | g x4; ga x2 | e x6 |
| Juniperus virginiana | Canis latrans | 6 | gf x5; a x1 | e x6 |
| Lepus americanus | Haliaeetus leucocephalus | 6 | g x5; ga x1 | e x6 |
| Marmota monax | Haliaeetus leucocephalus | 6 | g x5; ga x1 | e x6 |
| Megaptera novaeangliae | Haliaeetus leucocephalus | 6 | g x5; ga x1 | e x6 |
| Mustela erminea | Aquila chrysaetos | 6 | g x3; ga x3 | e x6 |
| Odocoileus hemionus | Taxidea taxus | 6 | ga x2; g x4 | e x6 |
| Phacochoerus africanus | Crocuta crocuta | 6 | g x6 | e x5, s x1 |
| Rangifer tarandus | Gulo gulo | 6 | g x6 | s x4, e x2 |
| Sciurus vulgaris | Vulpes vulpes | 6 | g x5; ga x1 | e x6 |
| Urocyon cinereoargenteus | Lynx rufus | 6 | g x5; ga x1 | e x6 |
| Urocyon cinereoargenteus | Puma concolor | 6 | ga x5; g x1 | e x6 |
| Acer pensylvanicum | Corvus corax | 5 | gf x4; gg x1 | e x5 |
| Acrididae | Canis latrans | 5 | ga x1; g x4 | e x5 |
| Aepyceros melampus | Crocodylus niloticus | 5 | g x4; ga x1 | e x5 |
| Alces alces | Aquila chrysaetos | 5 | ga x4; g x1 | e x5 |
| Alces alces | Lynx rufus | 5 | g x3; ga x2 | e x5 |
| Antilocapra americana | Puma concolor | 5 | ga x2; g x3 | e x5 |
| Atriplex canescens | Corvus corax | 5 | gf x2; gg x3 | e x5 |
| Capreolus capreolus | Felis silvestris | 5 | ga x3; g x2 | e x5 |
| Carnegiea gigantea | Neotoma albigula | 5 | gf x4; a x1 | e x5 |
| Cervus elaphus | Ursus arctos | 5 | g x5 | e x3, s x2 |
| Equus quagga | Crocodylus niloticus | 5 | g x3; ga x2 | e x5 |
| Equus quagga | Panthera pardus | 5 | g x4; ga x1 | e x5 |
| Glis glis | Canis lupus | 5 | ga x4; g x1 | e x5 |
| Lagopus lagopus | Ursus arctos | 5 | g x4; ga x1 | e x5 |
| Martes foina | Canis lupus | 5 | ga x3; g x2 | e x5 |
| Melanerpes formicivorus | Lynx rufus | 5 | g x4; ga x1 | e x5 |
| Ondatra zibethicus | Pituophis catenifer | 5 | g x4; ga x1 | e x5 |
| Pinus strobus | Corvus corax | 5 | g x4; ga x1 | e x5 |
| Pseudotsuga menziesii | Corvus corax | 5 | g x3; gf x2 | e x5 |
| Psidium cattleianum | Rattus rattus | 5 | gf x4; a x1 | e x5 |
| Quercus gambelii | Peromyscus maniculatus | 5 | gf x2; a x3 | e x5 |
| Quercus gambelii | Sciurus aberti | 5 | gf x4; a x1 | e x5 |
| Rangifer tarandus | Vulpes lagopus | 5 | g x3; ga x2 | e x4, s x1 |
| Sylvilagus audubonii | Puma concolor | 5 | g x4; ga x1 | e x5 |
| Syncerus caffer | Gyps africanus | 5 | g x4; ga x1 | s x3, e x2 |
| Thalassia testudinum | Sparisoma viride | 5 | g x2; ga x3 | e x5 |
| Thuja plicata | Corvus corax | 5 | g x4; ga x1 | e x5 |
| Ursus americanus | Canis lupus | 5 | g x2; ga x3 | e x5 |
| Vulpes vulpes | Haliaeetus leucocephalus | 5 | g x3; ga x2 | e x5 |
| Acinonyx jubatus | Panthera leo | 4 | g x2; ga x2 | e x4 |
| Acrididae | Buteo jamaicensis | 4 | ga x1; g x3 | e x4 |
| Aepyceros melampus | Gyps africanus | 4 | g x4 | s x3, e x1 |
| Alces alces | Martes americana | 4 | g x1; ga x3 | e x4 |
| Alectoris chukar | Canis lupus | 4 | ga x3; g x1 | e x4 |
| Amorpha canescens | Odocoileus virginianus | 4 | gf x3; a x1 | e x4 |
| Anas platyrhynchos | Canis lupus | 4 | g x1; ga x3 | e x4 |
| Antilocapra americana | Aquila chrysaetos | 4 | g x3; ga x1 | e x4 |
| Artemisia tridentata | Corvus corax | 4 | gf x2; gg x2 | e x4 |
| Canis aureus | Panthera pardus | 4 | g x3; ga x1 | e x4 |
| Capra hircus | Felis catus | 4 | g x2; ga x2 | e x4 |
| Capra ibex | Vulpes vulpes | 4 | g x2; ga x2 | s x2, e x2 |
| Capra sibirica | Vulpes vulpes | 4 | ga x1; g x3 | e x2, s x2 |
| Castor canadensis | Lynx canadensis | 4 | g x3; ga x1 | e x4 |
| Castor fiber | Vulpes vulpes | 4 | ga x3; g x1 | e x4 |
| Cervus canadensis | Aquila chrysaetos | 4 | ga x3; g x1 | e x4 |
| Cervus elaphus | Lynx rufus | 4 | g x3; ga x1 | e x4 |
| Connochaetes taurinus | Gyps africanus | 4 | g x4 | e x2, s x2 |
| Empetrum nigrum | Corvus corax | 4 | ga x1; g x3 | e x4 |
| Encelia farinosa | Lepus californicus | 4 | gf x3; a x1 | e x4 |
| Equus quagga | Gyps africanus | 4 | g x4 | s x3, e x1 |
| Fagus grandifolia | Halysidota tessellaris | 4 | g x3; ga x1 | e x4 |
| Glis glis | Ursus arctos | 4 | g x3; ga x1 | e x4 |
| Hippopotamus amphibius | Gyps africanus | 4 | g x3; ga x1 | e x3, s x1 |
| Hippopotamus amphibius | Necrosyrtes monachus | 4 | g x3; ga x1 | s x3, e x1 |
| Iguana iguana | Coragyps atratus | 4 | g x4 | s x1, e x3 |
| Larrea tridentata | Apis mellifera | 4 | gf x3; g x1 | e x4 |
| Lepus americanus | Aquila chrysaetos | 4 | g x3; ga x1 | e x4 |
| Lepus californicus | Puma concolor | 4 | g x1; ga x3 | e x4 |
| Lepus europaeus | Canis lupus | 4 | g x3; ga x1 | e x4 |
| Lepus timidus | Corvus corax | 4 | ga x3; g x1 | e x3, s x1 |
| Microtus ochrogaster | Lynx rufus | 4 | g x3; ga x1 | e x4 |
| Microtus pennsylvanicus | Haliaeetus leucocephalus | 4 | g x3; ga x1 | e x4 |
| Myodes glareolus | Canis lupus | 4 | ga x2; g x2 | e x4 |
| Myodes rufocanus | Ursus arctos | 4 | g x3; ga x1 | e x4 |
| Nucifraga caryocatactes | Vulpes vulpes | 4 | g x2; ga x2 | e x4 |
| Pecari tajacu | Leopardus pardalis | 4 | g x2; ga x2 | e x4 |
| Pinus sylvestris | Capreolus capreolus | 4 | ga x2; g x2 | e x4 |
| Populus tremuloides | Lepus americanus | 4 | g x3; ga x1 | e x4 |
| Pteronura brasiliensis | Panthera onca | 4 | g x3; ga x1 | e x4 |
| Quercus marilandica | Peromyscus leucopus | 4 | gf x3; a x1 | e x4 |
| Rangifer tarandus | Aquila chrysaetos | 4 | g x2; ga x2 | s x2, e x2 |
| Rubus spectabilis | Peromyscus maniculatus | 4 | gf x3; a x1 | e x4 |
| Rusa unicolor | Canis aureus | 4 | ga x1; g x3 | e x3, s x1 |
| Salix | Rangifer tarandus | 4 | ga x1; g x3 | e x4 |
| Sciurus vulgaris | Lynx lynx | 4 | g x2; ga x2 | e x4 |
| Vulpes lagopus | Ursus maritimus | 4 | g x2; ga x2 | e x4 |
| Vulpes vulpes | Lynx rufus | 4 | ga x2; g x2 | e x4 |
| Alces alces | Pekania pennanti | 3 | g x1; ga x2 | e x3 |
| Ammospermophilus leucurus | Cathartes aura | 3 | g x2; ga x1 | s x2, e x1 |
| Apodemus flavicollis | Lynx lynx | 3 | ga x2; g x1 | e x3 |
| Asclepias speciosa | Corvus corax | 3 | gf x1; gg x2 | e x3 |
| Ateles geoffroyi | Puma concolor | 3 | g x2; ga x1 | e x3 |
| Axis axis | Canis aureus | 3 | g x3 | e x2, s x1 |
| Brevoortia tyrannus | Haliaeetus leucocephalus | 3 | g x3 | e x2, s x1 |
| Canis latrans | Canis lupus | 3 | ga x2; g x1 | e x3 |
| Capra ibex | Canis lupus | 3 | ga x2; g x1 | e x3 |
| Capra sibirica | Aquila chrysaetos | 3 | gg x3 | e x2, s x1 |
| Carex | Rangifer tarandus | 3 | g x2; ga x1 | e x3 |
| Carpinus betulus | Parus major | 3 | g x1; ga x2 | e x3 |
| Castor canadensis | Puma concolor | 3 | ga x1; g x2 | e x3 |
| Cercocarpus montanus | Odocoileus hemionus | 3 | gf x1; a x2 | e x3 |
| Cervus canadensis | Ursus arctos | 3 | gg x3 | e x2, s x1 |
| Chamaenerion angustifolium | Lepus americanus | 3 | gf x1; a x2 | e x3 |
| Chionomys nivalis | Aquila chrysaetos | 3 | ga x2; g x1 | e x3 |
| Cirsium arvense | Corvus corax | 3 | gg x1; g x2 | e x3 |
| Connochaetes taurinus | Acinonyx jubatus | 3 | g x2; ga x1 | e x3 |
| Crotalus cerastes | Canis latrans | 3 | g x2; ga x1 | e x3 |
| Cuon alpinus | Panthera pardus | 3 | g x1; ga x2 | e x3 |
| Dasyprocta punctata | Coragyps atratus | 3 | g x3 | s x1, e x2 |
| Dasyprocta punctata | Puma concolor | 3 | ga x2; g x1 | e x3 |
| Equus quagga | Acinonyx jubatus | 3 | g x2; ga x1 | e x3 |
| Fagus sylvatica | Garrulus glandarius | 3 | g x2; ga x1 | e x3 |
| Garrulus glandarius | Vulpes vulpes | 3 | g x2; ga x1 | e x3 |
| Giraffa giraffa | Crocuta crocuta | 3 | ga x2; g x1 | e x3 |
| Glis glis | Lynx lynx | 3 | ga x2; g x1 | e x3 |
| Iguana iguana | Panthera onca | 3 | ga x2; g x1 | e x3 |
| Lagopus lagopus | Canis lupus | 3 | g x2; ga x1 | e x3 |
| Lagopus lagopus | Gulo gulo | 3 | g x2; ga x1 | e x3 |
| Lama guanicoe | Lycalopex culpaeus | 3 | g x3 | e x2, s x1 |
| Lepus europaeus | Buteo buteo | 3 | g x2; ga x1 | e x3 |
| Lepus timidus | Canis lupus | 3 | ga x2; g x1 | e x3 |
| Loxodonta africana | Lupulella mesomelas | 3 | g x3 | e x2, s x1 |
| Lupulella mesomelas | Panthera leo | 3 | g x2; ga x1 | e x3 |
| Macrocystis pyrifera | Orcinus orca | 3 | g x1; ga x2 | e x3 |
| Marmota marmota | Canis lupus | 3 | ga x1; g x2 | e x3 |
| Marmota marmota | Mustela erminea | 3 | g x2; ga x1 | e x3 |
| Martes americana | Ursus americanus | 3 | g x1; ga x2 | e x3 |
| Meles meles | Canis lupus | 3 | ga x2; g x1 | e x3 |
| Microtus oeconomus | Canis lupus | 3 | ga x1; g x2 | e x3 |
| Mustela erminea | Vulpes vulpes | 3 | g x2; ga x1 | e x3 |
| Myodes glareolus | Lynx lynx | 3 | ga x2; g x1 | e x3 |
| Nasua narica | Panthera onca | 3 | g x2; ga x1 | e x3 |
| Nucifraga columbiana | Buteo jamaicensis | 3 | g x2; ga x1 | e x3 |
| Odocoileus virginianus | Corvus brachyrhynchos | 3 | g x2; ga x1 | s x2, e x1 |
| Ondatra zibethicus | Lynx rufus | 3 | ga x1; g x2 | e x3 |
| Opuntia | Otospermophilus variegatus | 3 | ga x2; g x1 | e x3 |
| Opuntia polyacantha | Ovis canadensis | 3 | a x1; gf x2 | e x3 |
| Oryx gazella | Panthera leo | 3 | g x3 | e x2, s x1 |
| Ovis ammon | Vulpes vulpes | 3 | ga x2; g x1 | e x3 |
| Ovis dalli | Vulpes vulpes | 3 | ga x2; g x1 | e x3 |
| Pan troglodytes verus | Panthera pardus | 3 | g x1; ga x2 | e x3 |
| Papio anubis | Panthera leo | 3 | g x2; ga x1 | e x3 |
| Pekania pennanti | Lynx rufus | 3 | g x2; ga x1 | e x3 |
| Phoenicopterus roseus | Vulpes vulpes | 3 | g x2; ga x1 | e x3 |
| Picea glauca | Castor canadensis | 3 | g x1; ga x2 | e x3 |
| Piliocolobus badius | Panthera pardus | 3 | ga x2; g x1 | e x3 |
| Poaceae | Sus scrofa | 3 | g x2; ga x1 | e x3 |
| Quercus kelloggii | Peromyscus maniculatus | 3 | gf x2; a x1 | e x3 |
| Rhinoceros unicornis | Panthera tigris | 3 | g x2; ga x1 | e x3 |
| Rupicapra rupicapra | Gyps fulvus | 3 | a x3 | e x2, s x1 |
| Sylvilagus floridanus | Corvus brachyrhynchos | 3 | g x1; ga x2 | e x3 |
| Taxidea taxus | Puma concolor | 3 | ga x1; g x2 | e x3 |
| Thalassia testudinum | Diadema antillarum | 3 | ga x2; g x1 | e x3 |
| Tragelaphus scriptus | Crocuta crocuta | 3 | g x2; ga x1 | e x3 |
| Tragelaphus scriptus | Panthera pardus | 3 | g x2; ga x1 | e x3 |
| Urocitellus parryii | Vulpes vulpes | 3 | g x1; ga x2 | e x3 |
| Vaccinium myrtillus | Martes martes | 3 | g x2; ga x1 | e x3 |
| Vaccinium vitis-idaea | Rangifer tarandus | 3 | ga x1; g x2 | e x3 |
| Vulpes vulpes | Panthera uncia | 3 | g x1; ga x2 | e x3 |
| Vulpes vulpes | Puma concolor | 3 | g x2; ga x1 | e x3 |
| Abies alba | Capreolus capreolus | 2 | g x1; ga x1 | e x2 |
| Agkistrodon piscivorus | Alligator mississippiensis | 2 | g x1; ga x1 | e x2 |
| Ammospermophilus leucurus | Crotalus cerastes | 2 | g x1; ga x1 | e x2 |
| Anas platyrhynchos | Ursus arctos | 2 | g x1; ga x1 | e x2 |
| Anser caerulescens | Bubo scandiacus | 2 | g x1; ga x1 | e x2 |
| Anser caerulescens | Ursus maritimus | 2 | g x1; ga x1 | e x2 |
| Antilocapra americana | Haliaeetus leucocephalus | 2 | ga x1; g x1 | e x2 |
| Apodemus flavicollis | Ursus arctos | 2 | ga x1; g x1 | e x2 |
| Apodemus sylvaticus | Canis lupus | 2 | ga x1; g x1 | e x2 |
| Apodemus sylvaticus | Ursus arctos | 2 | ga x1; g x1 | e x2 |
| Aquila chrysaetos | Ursus arctos horribilis | 2 | ga x1; g x1 | e x2 |
| Arapaima gigas | Panthera onca | 2 | g x1; ga x1 | e x2 |
| Arctocephalus gazella | Macronectes giganteus | 2 | g x2 | s x1, e x1 |
| Arctocephalus pusillus | Lupulella mesomelas | 2 | g x2 | e x1, s x1 |
| Arctocephalus pusillus | Parahyaena brunnea | 2 | a x2 | e x1, s x1 |
| Arctostaphylos patula | Odocoileus hemionus | 2 | gg x1; gf x1 | e x2 |
| Ardea herodias | Lynx rufus | 2 | g x1; ga x1 | e x2 |
| Asclepias fascicularis | Anas platyrhynchos | 2 | gg x1; gf x1 | e x2 |
| Asclepias speciosa | Sturnus vulgaris | 2 | gf x1; gg x1 | e x2 |
| Asclepias syriaca | Passer domesticus | 2 | gf x1; g x1 | e x2 |
| Bacillariophyta | Copepoda | 2 | ga x1; g x1 | e x2 |
| Betula pubescens | Ursus arctos | 2 | ga x1; g x1 | e x2 |
| Bison bonasus | Canis lupus | 2 | g x1; ga x1 | e x2 |
| Boa imperator | Cathartes aura | 2 | g x2 | e x1, s x1 |
| Bradypus variegatus | Leopardus pardalis | 2 | g x1; ga x1 | e x2 |
| Bubalus bubalis | Varanus komodoensis | 2 | a x2 | e x1, s x1 |
| Bubo scandiacus | Ursus maritimus | 2 | g x1; ga x1 | e x2 |
| Budorcas taxicolor | Ursus thibetanus | 2 | a x2 | e x1, s x1 |
| Buteo jamaicensis | Haliaeetus leucocephalus | 2 | ga x1; g x1 | e x2 |
| Capra hircus | Ursus arctos | 2 | g x2 | e x1, s x1 |
| Capra walie | Crocuta crocuta | 2 | gg x2 | e x1, s x1 |
| Capreolus capreolus | Canis aureus | 2 | g x2 | s x1, e x1 |
| Carex | Capreolus capreolus | 2 | g x1; ga x1 | e x2 |
| Carnegiea gigantea | Ovis canadensis | 2 | gf x1; a x1 | e x2 |
| Carpinus betulus | Dendrocopos major | 2 | g x1; ga x1 | e x2 |
| Castor canadensis | Aquila chrysaetos | 2 | ga x1; g x1 | e x2 |
| Cervus canadensis | Pica hudsonia | 2 | ga x1; g x1 | e x1, s x1 |
| Chionomys nivalis | Corvus corax | 2 | ga x1; g x1 | e x2 |
| Civettictis civetta | Panthera pardus | 2 | g x1; ga x1 | e x2 |
| Connochaetes taurinus | Lupulella mesomelas | 2 | g x1; ga x1 | e x2 |
| Cylindropuntia imbricata | Ammotragus lervia | 2 | a x1; gf x1 | e x2 |
| Cynodon dactylon | Sus scrofa | 2 | ga x1; g x1 | e x2 |
| Dasyprocta punctata | Leopardus pardalis | 2 | g x1; ga x1 | e x2 |
| Dinaromys bogdanovi | Canis lupus | 2 | ga x1; g x1 | e x2 |
| Equisetum arvense | Corvus corax | 2 | g x1; ga x1 | e x2 |
| Equus quagga | Lupulella mesomelas | 2 | g x1; ga x1 | e x2 |
| Eremophila alpestris | Aquila chrysaetos | 2 | g x1; ga x1 | e x2 |
| Euphausia superba | Macronectes giganteus | 2 | g x1; ga x1 | e x2 |
| Fagus sylvatica | Columba palumbus | 2 | g x1; ga x1 | e x2 |
| Ficus | Cuniculus paca | 2 | ga x1; g x1 | e x2 |
| Ficus | Iguana iguana | 2 | g x1; ga x1 | e x2 |
| Ficus | Paradoxurus hermaphroditus | 2 | g x1; ga x1 | e x2 |
| Fulica atra | Ardea cinerea | 2 | g x1; ga x1 | e x2 |
| Gazella gazella | Canis aureus | 2 | gg x2 | e x1, s x1 |
| Gorilla gorilla gorilla | Panthera pardus | 2 | g x1; ga x1 | e x2 |
| Grus grus | Canis lupus | 2 | ga x1; g x1 | e x2 |
| Hippocamelus bisulcus | Lycalopex culpaeus | 2 | g x1; ga x1 | e x2 |
| Hippopotamus amphibius | Gypohierax angolensis | 2 | ga x1; g x1 | e x1, s x1 |
| Hippopotamus amphibius | Leptoptilos crumenifer | 2 | g x2 | e x1, s x1 |
| Iguana iguana | Harpia harpyja | 2 | g x1; ga x1 | e x2 |
| Juniperus virginiana | Sturnus vulgaris | 2 | gg x1; gf x1 | e x2 |
| Kobus ellipsiprymnus | Gyps africanus | 2 | g x2 | e x1, s x1 |
| Lanius excubitor | Varanus griseus | 2 | g x1; ga x1 | e x2 |
| Larix laricina | Castor canadensis | 2 | gf x1; a x1 | e x2 |
| Larix occidentalis | Corvus corax | 2 | gg x1; gf x1 | e x2 |
| Larus smithsonianus | Haliaeetus leucocephalus | 2 | g x1; ga x1 | e x2 |
| Lepus americanus | Gulo gulo | 2 | g x1; ga x1 | e x2 |
| Lepus americanus | Puma concolor | 2 | g x1; ga x1 | e x2 |
| Lepus tolai | Corvus corax | 2 | g x2 | s x1, e x1 |
| Lontra canadensis | Canis lupus | 2 | ga x1; g x1 | e x2 |
| Loxodonta africana | Leptoptilos crumenifer | 2 | g x2 | e x1, s x1 |
| Marmota himalayana | Gypaetus barbatus | 2 | a x2 | s x1, e x1 |
| Martes foina | Lynx lynx | 2 | g x1; ga x1 | e x2 |
| Martes martes | Lynx lynx | 2 | g x1; ga x1 | e x2 |
| Meles meles | Lynx lynx | 2 | ga x1; g x1 | e x2 |
| Miconia | Artibeus lituratus | 2 | g x1; ga x1 | e x2 |
| Miconia | Tapirus terrestris | 2 | g x1; ga x1 | e x2 |
| Morone saxatilis | Haliaeetus leucocephalus | 2 | g x1; ga x1 | s x1, e x1 |
| Mya truncata | Pusa hispida | 2 | g x1; ga x1 | e x2 |
| Myrcia | Tapirus terrestris | 2 | ga x1; g x1 | e x2 |
| Nucifraga caryocatactes | Martes zibellina | 2 | g x1; ga x1 | e x2 |
| Omocestus viridulus | Vulpes vulpes | 2 | g x1; ga x1 | e x2 |
| Oncorhynchus | Corvus corax | 2 | gg x2 | s x1, e x1 |
| Oncorhynchus | Orcinus orca | 2 | ga x1; g x1 | e x2 |
| Oncorhynchus spp. | Haliaeetus leucocephalus | 2 | g x2 | e x1, s x1 |
| Opuntia | Zenaida asiatica | 2 | ga x1; g x1 | e x2 |
| Opuntia engelmannii | Pecari tajacu | 2 | gf x1; a x1 | e x2 |
| Oreamnos americanus | Aquila chrysaetos | 2 | ga x1; g x1 | e x2 |
| Oreamnos americanus | Ursus americanus | 2 | ga x1; g x1 | e x2 |
| Oreamnos americanus | Ursus arctos | 2 | ga x1; g x1 | e x2 |
| Osphranter rufus | Aquila audax | 2 | g x2 | e x1, s x1 |
| Osphranter rufus | Canis dingo | 2 | a x2 | e x1, s x1 |
| Osphranter rufus | Varanus giganteus | 2 | a x2 | e x1, s x1 |
| Ovis ammon | Aegypius monachus | 2 | a x2 | s x1, e x1 |
| Ovis canadensis | Ursus arctos | 2 | ga x1; g x1 | e x2 |
| Papio ursinus | Panthera leo | 2 | g x1; ga x1 | e x2 |
| Parus major | Canis aureus | 2 | g x1; ga x1 | e x2 |
| Parus major | Martes martes | 2 | g x1; ga x1 | e x2 |
| Periphyton | Oreochromis | 2 | g x1; ga x1 | e x2 |
| Phragmites australis | Cygnus olor | 2 | ga x1; g x1 | e x2 |
| Poaceae | Odocoileus hemionus | 2 | g x1; ga x1 | e x2 |
| Prionailurus bengalensis | Panthera tigris | 2 | ga x1; g x1 | e x2 |
| Procavia capensis | Caracal caracal | 2 | g x1; ga x1 | e x2 |
| Procavia capensis | Gypaetus barbatus | 2 | a x2 | e x1, s x1 |
| Pseudoroegneria spicata | Microtus montanus | 2 | gf x1; a x1 | e x2 |
| Pseudoroegneria spicata | Odocoileus hemionus | 2 | gf x1; a x1 | e x2 |
| Psidium cattleianum | Himatione sanguinea | 2 | g x1; ga x1 | e x2 |
| Pteridium aquilinum | Corvus corax | 2 | g x1; ga x1 | e x2 |
| Pteropus conspicillatus | Haliastur indus | 2 | a x2 | e x1, s x1 |
| Pyrrhocorax graculus | Vulpes vulpes | 2 | g x1; ga x1 | e x2 |
| Quercus muehlenbergii | Peromyscus maniculatus | 2 | gf x1; a x1 | e x2 |
| Rangifer tarandus | Ursus americanus | 2 | g x1; ga x1 | e x2 |
| Rusa timorensis | Varanus komodoensis | 2 | a x2 | e x1, s x1 |
| Rusa unicolor | Neofelis nebulosa | 2 | g x1; ga x1 | e x2 |
| Schizachyrium scoparium | Odocoileus virginianus | 2 | gf x1; a x1 | e x2 |
| Sciurus carolinensis | Corvus brachyrhynchos | 2 | g x1; ga x1 | e x2 |
| Sorbus aucuparia | Martes martes | 2 | g x1; ga x1 | e x2 |
| Sorbus aucuparia | Vulpes vulpes | 2 | g x1; ga x1 | e x2 |
| Sparisoma viride | Sphyraena barracuda | 2 | ga x1; g x1 | e x2 |
| Sporobolus airoides | Dipodomys ordii | 2 | gf x1; a x1 | e x2 |
| Sus scrofa | Varanus komodoensis | 2 | a x2 | e x1, s x1 |
| Sylvicapra grimmia | Crocuta crocuta | 2 | ga x1; g x1 | e x2 |
| Sylvilagus audubonii | Athene cunicularia | 2 | g x1; ga x1 | e x2 |
| Sylvilagus floridanus | Circus hudsonius | 2 | g x1; ga x1 | e x2 |
| Syncerus caffer | Acinonyx jubatus | 2 | g x1; ga x1 | e x2 |
| Syzygium cumini | Canis aureus | 2 | ga x1; g x1 | e x2 |
| Trichosurus vulpecula | Mustela erminea | 2 | ga x1; g x1 | e x2 |
| Tsuga heterophylla | Odocoileus hemionus | 2 | ga x1; g x1 | e x2 |
| Urocyon cinereoargenteus | Panthera onca | 2 | g x1; ga x1 | e x2 |
| Ursus americanus | Canis latrans | 2 | ga x1; g x1 | e x2 |
| Vulpes vulpes | Ursus arctos horribilis | 2 | ga x1; g x1 | e x2 |
